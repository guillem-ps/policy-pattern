"""
Evaluator: resolves check() over a CompiledModel and a TupleStore.
"""

from dataclasses import dataclass, field

from .errors import EvaluationError, UnknownNameError, UnknownTypeError
from .models import (
    CompiledModel,
    DirectSubject,
    Exclusion,
    Intersection,
    ObjectReference,
    PermissionExpression,
    Reference,
    Subject,
    SubjectSet,
    TupleToUserset,
    Union,
)
from .ports import TupleStore, View


@dataclass(frozen=True, slots=True)
class EvaluationBudget:
    """
    Per-`check()` resource limits.

    No `__post_init__` validation — a degenerate value (e.g. `max_depth=0`)
    is well-defined without a guard: it simply fails on the first node
    `Evaluator` visits. Same reasoning already applied to `read_relation`'s
    `limit=0` — no invariant to enforce, trust the caller.

    Example:
        EvaluationBudget(max_depth=10, max_nodes=500, max_store_reads=100)
    """

    # Maximum recursion depth for a single `check()` call. Each recursive call
    # to `_check_name()` adds one to the depth; exceeding this limit raises an
    # `EvaluationError`.
    max_depth: int = 25

    # Maximum number of nodes visited during a single `check()` call. Each
    # call to `_check_name()` increments this count; exceeding this limit raises an `EvaluationError`.
    max_nodes: int = 10_000

    # Maximum number of store reads during a single `check()` call. Each call
    # to `_charge_read()` increments this count; exceeding this limit raises an `EvaluationError`.
    max_store_reads: int = 1_000


@dataclass(slots=True)
class EvaluationContext:
    """
    Live bookkeeping for exactly one `check()` call.

    Deliberately mutable, unlike almost everything else in this package —
    this is not a domain value, it is the in-flight state of one
    evaluation, never seen or reused outside that call's lifetime.

    `len(visited)` doubles as the current recursion depth: `visited` only
    ever holds ancestors currently in progress on the live call path
    (added before recursing, discarded after returning) — anything
    permanently resolved lives in `memo` instead, so the two never overlap
    in meaning.
    """

    view: View
    budget: EvaluationBudget
    visited: set[tuple[ObjectReference, str]] = field(default_factory=lambda: set[tuple[ObjectReference, str]]())
    memo: dict[tuple[ObjectReference, str], bool] = field(
        default_factory=lambda: dict[tuple[ObjectReference, str], bool]()
    )
    node_count: int = 0
    store_read_count: int = 0


class Evaluator:
    """
    Resolves check(subject, name, object) against a CompiledModel and a TupleStore.

    Example:
        evaluator = Evaluator(model=compiled_model, store=memory_store)
        evaluator.check(subject, "viewer", document)
    """

    def __init__(self, model: CompiledModel, store: TupleStore) -> None:
        """
        Binds this evaluator to one CompiledModel and one TupleStore.
        """
        self._model = model
        self._store = store

    def check(
        self,
        subject: Subject,
        name: str,
        object: ObjectReference,
        budget: EvaluationBudget | None = None,
    ) -> bool:
        """
        Returns whether subject holds relation/permission name on object.

        Opens exactly one store.snapshot() for the lifetime of this call —
        docs/semantics.md's snapshot-consistency requirement — every read
        this call triggers, however deep the recursion, goes through the
        same View.

        `budget` defaults to `None`/`EvaluationBudget()` rather than a
        bare `EvaluationBudget()` default argument — Python evaluates a
        default argument once, at function-definition time, so every
        omitted-budget call would share one instance. Harmless here since
        `EvaluationBudget` is frozen, but `ruff`'s `B008` flags the pattern
        regardless of mutability, and the codebase doesn't carve out an
        exception for "this particular immutable case."
        """
        if budget is None:
            budget = EvaluationBudget()
        with self._store.snapshot() as view:
            context = EvaluationContext(view=view, budget=budget)
            return self._check_name(subject, name, object, context)

    def _check_name(self, subject: Subject, name: str, object: ObjectReference, context: EvaluationContext) -> bool:
        """
        Dispatches (object, name) to a relation or permission check, with cycle/memo/budget bookkeeping.
        """
        key = (object, name)
        if key in context.memo:
            return context.memo[key]
        if key in context.visited:
            raise EvaluationError(
                message=f"cycle detected: {name!r} on {object!r} is already being evaluated for {subject!r}",
                related=f"object={object!r}",
            )

        if len(context.visited) >= context.budget.max_depth:
            raise EvaluationError(
                message=f"max_depth={context.budget.max_depth!r} exceeded evaluating {name!r} on {object!r}",
                related=f"object={object!r}",
            )
        context.node_count += 1
        if context.node_count > context.budget.max_nodes:
            raise EvaluationError(
                message=f"max_nodes={context.budget.max_nodes!r} exceeded evaluating {name!r} on {object!r}",
                related=f"object={object!r}",
            )

        context.visited.add(key)
        try:
            try:
                type_declaration = self._model.types[object.type]
            except KeyError:
                raise UnknownTypeError(
                    message=f"type {object.type!r} is not declared in this CompiledModel",
                    related=f"object={object!r}",
                ) from None
            if name in type_declaration.relations:
                result = self._check_relation(subject, name, object, context)
            elif name in type_declaration.permissions:
                result = self._check_permission(subject, type_declaration.permissions[name], object, context)
            else:
                raise UnknownNameError(
                    message=f"{name!r} is not declared as a relation or permission on {object.type!r}",
                    related=f"object={object!r}",
                )
        finally:
            context.visited.discard(key)

        context.memo[key] = result
        return result

    def _check_relation(self, subject: Subject, name: str, object: ObjectReference, context: EvaluationContext) -> bool:
        """
        Exact tuple lookup, then bounded userset expansion for any SubjectSet found.

        Every candidate subject's shape is checked against this Relation's
        own `allowed_subject_types` before it counts — `TupleStore` is
        schema-agnostic by design (docs/architecture.md), so it never
        rejects a malformed write; this is the one place that knows both
        the schema and the stored fact, so it is the actual trust boundary.
        A tuple whose subject shape isn't declared is inert: never a match,
        never followed.
        """
        relation = self._model.types[object.type].relations[name]

        def shape_allowed(candidate: Subject) -> bool:
            if isinstance(candidate, DirectSubject):
                return candidate.object.type in relation.allowed_subject_types
            return f"{candidate.object.type}#{candidate.relation}" in relation.allowed_subject_types

        self._charge_read(context, object, name)
        if shape_allowed(subject) and context.view.read_tuple(subject, name, object):
            return True

        self._charge_read(context, object, name)
        result = context.view.read_relation(object, name, limit=context.budget.max_nodes - context.node_count)
        if not result.complete:
            raise EvaluationError(
                message=f"enumeration of {name!r} on {object!r} truncated by remaining max_nodes budget",
                related=f"object={object!r}",
            )

        return any(
            isinstance(t.subject, SubjectSet)
            and shape_allowed(t.subject)
            and self._check_name(subject, t.subject.relation, t.subject.object, context)
            for t in sorted(result.tuples, key=repr)
        )

    def _check_permission(
        self, subject: Subject, expression: PermissionExpression, object: ObjectReference, context: EvaluationContext
    ) -> bool:
        """
        Recursively evaluates a PermissionExpression tree.

        Union/Intersection may use Python's or/and directly: if the left
        operand already decides the boolean result, skipping the right one
        cannot produce an incorrect decision (docs/semantics.md forbids
        short-circuiting only for Exclusion, where skipping `exclude` could
        hide a real subtraction). Python's or/and evaluate left-to-right by
        language specification, satisfying the determinism requirement for
        free.
        """
        if isinstance(expression, Reference):
            return self._check_name(subject, expression.name, object, context)
        if isinstance(expression, TupleToUserset):
            return self._check_tuple_to_userset(subject, expression, object, context)
        if isinstance(expression, (Union, Intersection)):
            left = self._check_permission(subject, expression.left, object, context)
            if isinstance(expression, Union):
                return left or self._check_permission(subject, expression.right, object, context)
            return left and self._check_permission(subject, expression.right, object, context)
        if isinstance(expression, Exclusion):
            include = self._check_permission(subject, expression.include, object, context)
            exclude = self._check_permission(subject, expression.exclude, object, context)
            return include and not exclude
        raise EvaluationError(
            message=f"unknown expression type {type(expression).__name__!r}",
            related=f"object={object!r}",
        )

    def _check_tuple_to_userset(
        self, subject: Subject, expression: TupleToUserset, object: ObjectReference, context: EvaluationContext
    ) -> bool:
        """
        Follows expression.tupleset to each related object, then checks expression.computed there.

        Only DirectSubject entries are followed — a SubjectSet stored under
        the tupleset relation has no single "related object" to jump to, so
        it does not participate in traversal. A DirectSubject whose type
        isn't declared in the tupleset Relation's own `allowed_subject_types`
        is malformed data and is skipped the same way `_check_relation`
        skips a malformed direct/userset match.
        """
        relation = self._model.types[object.type].relations[expression.tupleset]

        self._charge_read(context, object, expression.tupleset)
        result = context.view.read_relation(
            object, expression.tupleset, limit=context.budget.max_nodes - context.node_count
        )
        if not result.complete:
            raise EvaluationError(
                message=f"enumeration of {expression.tupleset!r} on {object!r} truncated by remaining max_nodes budget",
                related=f"object={object!r}",
            )

        return any(
            isinstance(t.subject, DirectSubject)
            and t.subject.object.type in relation.allowed_subject_types
            and self._check_name(subject, expression.computed, t.subject.object, context)
            for t in sorted(result.tuples, key=repr)
        )

    def _charge_read(self, context: EvaluationContext, object: ObjectReference, name: str) -> None:
        """
        Counts one store read, raising EvaluationError if max_store_reads is now exceeded.
        """
        context.store_read_count += 1
        if context.store_read_count > context.budget.max_store_reads:
            raise EvaluationError(
                message=(
                    f"max_store_reads={context.budget.max_store_reads!r} exceeded evaluating {name!r} on {object!r}"
                ),
                related=f"object={object!r}",
            )
