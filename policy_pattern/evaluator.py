"""
Evaluator: resolves check() over a CompiledModel and a TupleStore.
"""

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field
from functools import cached_property

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
    Resource limits for one `check()` or `check_many()` call.

    `max_nodes` and `max_store_reads` accumulate across a `check_many()` call.
    `max_depth` bounds the live `context.visited` frontier and resets as each
    request finishes, so it does not accumulate across the batch.

    No `__post_init__` validation — a degenerate value (e.g. `max_depth=0`)
    is well-defined without a guard: it simply fails on the first node
    `Evaluator` visits. Same reasoning already applied to `read_relation`'s
    `limit=0` — no invariant to enforce, trust the caller.

    Example:
        EvaluationBudget(max_depth=10, max_nodes=500, max_store_reads=100)
    """

    # Maximum recursion depth for one call. Each recursive call
    # to `_check_name()` adds one to the depth; exceeding this limit raises an
    # `EvaluationError`.
    max_depth: int = 25

    # Maximum number of nodes visited during one call. Each
    # call to `_check_name()` increments this count; exceeding this limit raises an `EvaluationError`.
    max_nodes: int = 10_000

    # Maximum number of store reads during one call. Each call
    # to `_charge_read()` increments this count; exceeding this limit raises an `EvaluationError`.
    max_store_reads: int = 1_000


@dataclass(slots=True)
class EvaluationContext:
    """
    Live bookkeeping for exactly one `check()` or `check_many()` call.

    Deliberately mutable, unlike almost everything else in this package —
    this is not a domain value, it is the in-flight state of one
    evaluation, never seen or reused outside that call's lifetime.

    `len(visited)` doubles as the current recursion depth: `visited` only
    ever holds ancestors currently in progress on the live call path
    (added before recursing, discarded after returning) — anything
    permanently resolved lives in `memo` instead, so the two never overlap
    in meaning.

    The key carries the subject because one `check()` has a constant subject,
    while `check_many()` can mix subjects; a narrower key could reuse one
    subject's cached decision for another and cause a false allow.
    """

    view: View
    budget: EvaluationBudget
    visited: set[tuple[Subject, ObjectReference, str]] = field(
        default_factory=lambda: set[tuple[Subject, ObjectReference, str]]()
    )
    memo: dict[tuple[Subject, ObjectReference, str], bool] = field(
        default_factory=lambda: dict[tuple[Subject, ObjectReference, str], bool]()
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

    def check_many(
        self,
        requests: Sequence[tuple[Subject, str, ObjectReference]],
        budget: EvaluationBudget | None = None,
    ) -> list[bool]:
        """
        Returns one decision per request, preserving input order and duplicates.

        The whole batch shares one snapshot, context, and budget. An error on
        any request aborts the call and propagates without partial results.
        """
        if budget is None:
            budget = EvaluationBudget()
        with self._store.snapshot() as view:
            context = EvaluationContext(view=view, budget=budget)
            return [self._check_name(subject, name, object, context) for subject, name, object in requests]

    def list_objects(
        self,
        subject: Subject,
        name: str,
        object_type: str,
        candidate_ids: frozenset[ObjectReference] | None = None,
        budget: EvaluationBudget | None = None,
    ) -> frozenset[ObjectReference]:
        """Returns objects of `object_type` on which `subject` holds `name`.

        Args:
            subject (Subject): The subject whose access is queried.
            name (str): The relation or permission name to check.
            object_type (str): The type of objects to return.
            candidate_ids (frozenset[ObjectReference] | None): Optional objects to check instead of discovering them.
            budget (EvaluationBudget | None): Resource limits for this evaluation.

        Returns:
            frozenset[ObjectReference]: Objects of `object_type` allowed by the forward check.

        Raises:
            UnknownTypeError: If `object_type` is not declared in the CompiledModel.
            UnknownNameError: If `name` is not declared on `object_type`.
            EvaluationError: If reverse candidate discovery or a candidate check exhausts the evaluation budget.
        """
        if object_type not in self._model.types:
            raise UnknownTypeError(
                message=f"type {object_type!r} is not declared in this CompiledModel",
                related=f"object_type={object_type!r}",
            )
        declaration = self._model.types[object_type]
        if name not in declaration.relations and name not in declaration.permissions:
            raise UnknownNameError(
                message=f"{name!r} is not declared as a relation or permission on {object_type!r}",
                related=f"object_type={object_type!r}",
            )

        if budget is None:
            budget = EvaluationBudget()

        with self._store.snapshot() as view:
            context = EvaluationContext(view=view, budget=budget)
            candidates = self._reverse_candidates(subject, context) if candidate_ids is None else candidate_ids

            return frozenset(
                object
                for object in sorted(candidates, key=repr)
                if object.type == object_type and self._check_name(subject, name, object, context)
            )

    def _reverse_candidates(self, subject: Subject, context: EvaluationContext) -> frozenset[ObjectReference]:
        """Walk tuple subject edges to generate possible objects without interpreting permissions.

        Args:
            subject (Subject): The starting subject for the reverse walk.
            context (EvaluationContext): The shared view and resource-budget state.

        Returns:
            frozenset[ObjectReference]: All candidate objects reached by the tuple walk.

        Raises:
            EvaluationError: If `max_depth` or `max_nodes` is exceeded, or a subject-keyed enumeration is truncated.
        """
        queue: deque[tuple[Subject, int]] = deque([(subject, 0)])
        visited: set[Subject] = {subject}
        candidates: set[ObjectReference] = set()

        while queue:
            current, depth = queue.popleft()
            context.node_count += 1
            if context.node_count > context.budget.max_nodes:
                raise EvaluationError(
                    message=f"max_nodes={context.budget.max_nodes!r} exceeded during reverse lookup",
                    related=f"subject={current!r}",
                )

            self._charge_read(context, current.object, "list_objects")
            result = context.view.read_tuples_for_subject(
                current,
                limit=context.budget.max_nodes - context.node_count,
            )

            if not result.complete:
                raise EvaluationError(
                    message=(f"enumeration for subject {current!r} truncated by remaining max_nodes budget"),
                    related=f"subject={current!r}",
                )

            if result.tuples and depth >= context.budget.max_depth:
                raise EvaluationError(
                    message=(f"max_depth={context.budget.max_depth!r} exceeded during reverse lookup from {current!r}"),
                    related=f"subject={current!r}",
                )

            for tuple_ in sorted(result.tuples, key=repr):
                candidates.add(tuple_.object)
                for next_subject in self._reverse_frontier(tuple_.object):
                    if next_subject not in visited:
                        visited.add(next_subject)
                        queue.append((next_subject, depth + 1))

        return frozenset(candidates)

    @cached_property
    def _referenceable_shapes(self) -> frozenset[str]:
        """Return the subject shapes referenced by any relation in the model.

        Returns:
            frozenset[str]: Subject type and type/relation shapes allowed by model relations.

        Raises:
            None.
        """
        return frozenset(
            allowed_shape
            for type_declaration in self._model.types.values()
            for relation in type_declaration.relations.values()
            for allowed_shape in relation.allowed_subject_types
        )

    def _reverse_frontier(self, object: ObjectReference) -> tuple[Subject, ...]:
        """Return the declared subject identities that may reference `object`.

        Args:
            object (ObjectReference): The object whose possible subject identities are generated.

        Returns:
            tuple[Subject, ...]: Direct and userset identities that model relations may reference.

        Raises:
            None.
        """
        next_subjects: list[Subject] = []
        if object.type in self._referenceable_shapes:
            next_subjects.append(DirectSubject(object=object))

        declaration = self._model.types.get(object.type)
        if declaration is None:
            return tuple(next_subjects)

        names = (*declaration.relations, *declaration.permissions)
        next_subjects.extend(
            [
                SubjectSet(object=object, relation=name)
                for name in names
                if f"{object.type}#{name}" in self._referenceable_shapes
            ]
        )
        return tuple(next_subjects)

    def _check_name(self, subject: Subject, name: str, object: ObjectReference, context: EvaluationContext) -> bool:
        """
        Dispatches (object, name) to a relation or permission check, with cycle/memo/budget bookkeeping.
        """
        key = (subject, object, name)
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
