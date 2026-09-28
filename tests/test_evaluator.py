"""
Test module for evaluator.py.
"""

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import FrozenInstanceError
from typing import override

from pytest import raises

from policy_pattern.adapters.memory import MemoryTupleStore
from policy_pattern.errors import EvaluationError, UnknownNameError, UnknownTypeError
from policy_pattern.evaluator import EvaluationBudget, EvaluationContext, Evaluator
from policy_pattern.models import (
    CompiledModel,
    DirectSubject,
    Exclusion,
    Intersection,
    Mutation,
    ObjectReference,
    PermissionExpression,
    Reference,
    Relation,
    SubjectSet,
    Tuple,
    TupleToUserset,
    Type,
    Union,
)
from policy_pattern.ports import TupleStore, View


def test_evaluation_budget_default_values() -> None:
    """
    Test that EvaluationBudget uses the documented defaults when constructed with no arguments.
    """
    budget = EvaluationBudget()
    assert budget.max_depth == 25
    assert budget.max_nodes == 10_000
    assert budget.max_store_reads == 1_000


def test_evaluation_budget_equality() -> None:
    """
    Test that two EvaluationBudget instances with the same field values are equal.
    """
    assert EvaluationBudget(max_depth=5, max_nodes=10, max_store_reads=20) == EvaluationBudget(
        max_depth=5, max_nodes=10, max_store_reads=20
    )


def test_evaluation_budget_inequality_different_max_depth() -> None:
    """
    Test that two EvaluationBudget instances with a different max_depth are not equal.
    """
    assert EvaluationBudget(max_depth=5) != EvaluationBudget(max_depth=6)


def test_evaluation_budget_hash_consistency() -> None:
    """
    Test that equal EvaluationBudget instances have the same hash value.
    """
    assert hash(EvaluationBudget(max_depth=5)) == hash(EvaluationBudget(max_depth=5))


def test_evaluation_budget_is_frozen() -> None:
    """
    Test that EvaluationBudget instances cannot be mutated after construction.
    """
    budget = EvaluationBudget()

    with raises(FrozenInstanceError):
        budget.max_depth = 1  # ty: ignore[invalid-assignment]

    with raises(FrozenInstanceError):
        budget.max_nodes = 1  # ty: ignore[invalid-assignment]

    with raises(FrozenInstanceError):
        budget.max_store_reads = 1  # ty: ignore[invalid-assignment]


def test_evaluation_context_starts_empty() -> None:
    """
    Test that a fresh EvaluationContext has no visited/memo entries and zero counters.
    """
    store = MemoryTupleStore()
    with store.snapshot() as view:
        context = EvaluationContext(view=view, budget=EvaluationBudget())

        assert context.visited == set()
        assert context.memo == {}
        assert context.node_count == 0
        assert context.store_read_count == 0


def test_evaluation_context_is_mutable() -> None:
    """
    Test that EvaluationContext fields can be mutated in place — it is deliberately not frozen.
    """
    store = MemoryTupleStore()
    with store.snapshot() as view:
        context = EvaluationContext(view=view, budget=EvaluationBudget())
        context.node_count += 1
        context.store_read_count += 1

        assert context.node_count == 1
        assert context.store_read_count == 1


def _direct(id_: str) -> DirectSubject:
    return DirectSubject(object=ObjectReference(type="user", id=id_))


def _group(id_: str) -> ObjectReference:
    return ObjectReference(type="group", id=id_)


def _group_model() -> CompiledModel:
    return CompiledModel(
        types={
            "group": Type(
                name="group",
                relations={"member": Relation(allowed_subject_types=("user", "group#member"))},
                permissions={},
            ),
        }
    )


class _SnapshotCountingStore(TupleStore):
    def __init__(self, inner: TupleStore) -> None:
        self._inner = inner
        self.snapshot_count = 0

    @override
    def write_tuples(self, mutation: Mutation) -> None:
        self._inner.write_tuples(mutation)

    @override
    @contextmanager
    def snapshot(self) -> Generator[View, None, None]:
        self.snapshot_count += 1
        with self._inner.snapshot() as view:
            yield view


def test_check_direct_relation_exact_match() -> None:
    """
    Test that check() returns True for an exact stored tuple match on a bare Relation.
    """
    model = _group_model()
    store = MemoryTupleStore()
    alice = _direct("alice")
    group_a = _group("a")
    store.write_tuples(
        Mutation(additions=frozenset({Tuple(subject=alice, relation="member", object=group_a)}), deletions=frozenset())
    )
    evaluator = Evaluator(model=model, store=store)

    assert evaluator.check(alice, "member", group_a) is True


def test_check_direct_relation_no_match() -> None:
    """
    Test that check() returns False when no tuple and no userset expansion matches.
    """
    model = _group_model()
    store = MemoryTupleStore()
    evaluator = Evaluator(model=model, store=store)

    assert evaluator.check(_direct("alice"), "member", _group("a")) is False


def test_check_relation_expands_userset() -> None:
    """
    Test that check() recursively follows a SubjectSet tuple to prove indirect membership.

    group:a#member@group:b#member, and alice is a direct member of
    group:b — alice must also count as a member of group:a.
    """
    model = _group_model()
    store = MemoryTupleStore()
    alice = _direct("alice")
    group_a = _group("a")
    group_b = _group("b")
    nested = SubjectSet(object=group_b, relation="member")
    store.write_tuples(
        Mutation(
            additions=frozenset(
                {
                    Tuple(subject=nested, relation="member", object=group_a),
                    Tuple(subject=alice, relation="member", object=group_b),
                }
            ),
            deletions=frozenset(),
        )
    )
    evaluator = Evaluator(model=model, store=store)

    assert evaluator.check(alice, "member", group_a) is True


def test_check_relation_checking_a_subject_set_itself() -> None:
    """
    Test that check()'s subject argument can itself be a SubjectSet, not only a DirectSubject.

    Does group:eng#member hold member on group:leads? — a legitimate
    nested-group query, never exercised if every test only checks a
    DirectSubject.
    """
    model = _group_model()
    store = MemoryTupleStore()
    eng_members = SubjectSet(object=_group("eng"), relation="member")
    leads = _group("leads")
    store.write_tuples(
        Mutation(
            additions=frozenset({Tuple(subject=eng_members, relation="member", object=leads)}), deletions=frozenset()
        )
    )
    evaluator = Evaluator(model=model, store=store)

    assert evaluator.check(eng_members, "member", leads) is True


def test_check_relation_cycle_raises_evaluation_error() -> None:
    """
    Test that a mutual userset cycle (group:a#member -> group:b#member -> group:a#member) raises EvaluationError.
    """
    model = _group_model()
    store = MemoryTupleStore()
    group_a = _group("a")
    group_b = _group("b")
    store.write_tuples(
        Mutation(
            additions=frozenset(
                {
                    Tuple(subject=SubjectSet(object=group_b, relation="member"), relation="member", object=group_a),
                    Tuple(subject=SubjectSet(object=group_a, relation="member"), relation="member", object=group_b),
                }
            ),
            deletions=frozenset(),
        )
    )
    evaluator = Evaluator(model=model, store=store)

    with raises(EvaluationError):
        evaluator.check(_direct("alice"), "member", group_a)


def _chain_of_groups(length: int) -> list[ObjectReference]:
    return [_group(str(i)) for i in range(length)]


def test_check_relation_max_depth_exceeded_raises() -> None:
    """
    Test that a userset chain deeper than max_depth raises EvaluationError.
    """
    model = _group_model()
    store = MemoryTupleStore()
    chain = _chain_of_groups(5)
    additions = {
        Tuple(subject=SubjectSet(object=chain[i + 1], relation="member"), relation="member", object=chain[i])
        for i in range(len(chain) - 1)
    }
    additions.add(Tuple(subject=_direct("alice"), relation="member", object=chain[-1]))
    store.write_tuples(Mutation(additions=frozenset(additions), deletions=frozenset()))
    evaluator = Evaluator(model=model, store=store)

    with raises(EvaluationError):
        evaluator.check(_direct("alice"), "member", chain[0], budget=EvaluationBudget(max_depth=2))


def test_check_relation_max_nodes_exceeded_via_node_count_raises() -> None:
    """
    Test that node_count exceeding max_nodes raises EvaluationError even without a truncated read.

    Each group in the chain has exactly one SubjectSet child, so
    read_relation never truncates — this isolates _check_name's own
    node_count check from the enumeration-truncation path below.
    """
    model = _group_model()
    store = MemoryTupleStore()
    chain = _chain_of_groups(5)
    additions = {
        Tuple(subject=SubjectSet(object=chain[i + 1], relation="member"), relation="member", object=chain[i])
        for i in range(len(chain) - 1)
    }
    additions.add(Tuple(subject=_direct("alice"), relation="member", object=chain[-1]))
    store.write_tuples(Mutation(additions=frozenset(additions), deletions=frozenset()))
    evaluator = Evaluator(model=model, store=store)

    with raises(EvaluationError):
        evaluator.check(_direct("alice"), "member", chain[0], budget=EvaluationBudget(max_nodes=2, max_depth=100))


def test_check_relation_enumeration_truncated_raises() -> None:
    """
    Test that a truncated userset enumeration always raises, even if none of the examined tuples matched.

    Five branches under one group, max_nodes bounds read_relation's limit
    to fewer than five — the result must never be silently read as "no
    match found."
    """
    model = _group_model()
    store = MemoryTupleStore()
    root = _group("root")
    branches = [_group(f"branch{i}") for i in range(5)]
    additions = {
        Tuple(subject=SubjectSet(object=branch, relation="member"), relation="member", object=root)
        for branch in branches
    }
    store.write_tuples(Mutation(additions=frozenset(additions), deletions=frozenset()))
    evaluator = Evaluator(model=model, store=store)

    with raises(EvaluationError):
        evaluator.check(_direct("alice"), "member", root, budget=EvaluationBudget(max_nodes=2))


def test_check_relation_max_store_reads_exceeded_raises() -> None:
    """
    Test that exceeding max_store_reads raises EvaluationError — the gap Decision 8 exists to close.
    """
    model = _group_model()
    store = MemoryTupleStore()
    chain = _chain_of_groups(5)
    additions = {
        Tuple(subject=SubjectSet(object=chain[i + 1], relation="member"), relation="member", object=chain[i])
        for i in range(len(chain) - 1)
    }
    additions.add(Tuple(subject=_direct("alice"), relation="member", object=chain[-1]))
    store.write_tuples(Mutation(additions=frozenset(additions), deletions=frozenset()))
    evaluator = Evaluator(model=model, store=store)

    with raises(EvaluationError):
        evaluator.check(
            _direct("alice"),
            "member",
            chain[0],
            budget=EvaluationBudget(max_store_reads=2, max_depth=100, max_nodes=1000),
        )


def test_check_degenerate_budget_raises_evaluation_error_not_something_else() -> None:
    """
    Test that a degenerate EvaluationBudget (max_nodes=0) fails cleanly with EvaluationError.
    """
    model = _group_model()
    store = MemoryTupleStore()
    evaluator = Evaluator(model=model, store=store)

    with raises(EvaluationError):
        evaluator.check(_direct("alice"), "member", _group("a"), budget=EvaluationBudget(max_nodes=0))


def test_check_raises_unknown_type_error_for_undeclared_object_type() -> None:
    """
    Test that check() raises UnknownTypeError when object.type is not declared in the CompiledModel.
    """
    model = _group_model()
    store = MemoryTupleStore()
    evaluator = Evaluator(model=model, store=store)

    with raises(UnknownTypeError):
        evaluator.check(_direct("alice"), "member", ObjectReference(type="document", id="42"))


def test_check_raises_unknown_type_error_via_userset_expansion() -> None:
    """
    Test that userset expansion into a SubjectSet with an undeclared object.type raises UnknownTypeError.
    """
    model = _group_model()
    store = MemoryTupleStore()
    group_a = _group("a")
    undeclared = SubjectSet(object=ObjectReference(type="document", id="42"), relation="member")
    store.write_tuples(
        Mutation(
            additions=frozenset({Tuple(subject=undeclared, relation="member", object=group_a)}), deletions=frozenset()
        )
    )
    evaluator = Evaluator(model=model, store=store)

    with raises(UnknownTypeError):
        evaluator.check(_direct("alice"), "member", group_a)


def test_check_raises_unknown_name_error_for_undeclared_name() -> None:
    """
    Test that check() raises UnknownNameError (not a raw KeyError) for a name declared nowhere on the type.
    """
    model = _group_model()
    store = MemoryTupleStore()
    evaluator = Evaluator(model=model, store=store)

    with raises(UnknownNameError):
        evaluator.check(_direct("alice"), "not_a_real_relation_or_permission", _group("a"))


def test_check_opens_exactly_one_snapshot() -> None:
    """
    Test that check() opens exactly one store.snapshot(), even when internal evaluation issues multiple reads.
    """
    model = _group_model()
    inner = MemoryTupleStore()
    group_a = _group("a")
    group_b = _group("b")
    inner.write_tuples(
        Mutation(
            additions=frozenset(
                {
                    Tuple(subject=SubjectSet(object=group_b, relation="member"), relation="member", object=group_a),
                    Tuple(subject=_direct("alice"), relation="member", object=group_b),
                }
            ),
            deletions=frozenset(),
        )
    )
    store = _SnapshotCountingStore(inner)
    evaluator = Evaluator(model=model, store=store)

    evaluator.check(_direct("alice"), "member", group_a)

    assert store.snapshot_count == 1


def _document(id_: str) -> ObjectReference:
    return ObjectReference(type="document", id=id_)


def _document_model() -> CompiledModel:
    return CompiledModel(
        types={
            "document": Type(
                name="document",
                relations={
                    "owner": Relation(allowed_subject_types=("user",)),
                    "editor": Relation(allowed_subject_types=("user",)),
                    "blocked": Relation(allowed_subject_types=("user",)),
                },
                permissions={
                    "viewer": Union(left=Reference(name="owner"), right=Reference(name="editor")),
                    "manager": Intersection(left=Reference(name="owner"), right=Reference(name="editor")),
                    "restricted_viewer": Exclusion(include=Reference(name="owner"), exclude=Reference(name="blocked")),
                },
            ),
        }
    )


def test_check_permission_reference_dispatches_to_relation() -> None:
    """
    Test that a Reference permission resolves to the named relation.
    """
    model = _document_model()
    store = MemoryTupleStore()
    document = _document("42")
    alice = _direct("alice")
    store.write_tuples(
        Mutation(additions=frozenset({Tuple(subject=alice, relation="owner", object=document)}), deletions=frozenset())
    )
    evaluator = Evaluator(model=model, store=store)

    assert evaluator.check(alice, "viewer", document) is True


def test_check_permission_union_true_via_either_branch() -> None:
    """
    Test that Union is True when either operand holds, False when neither does.
    """
    model = _document_model()
    store = MemoryTupleStore()
    document = _document("42")
    alice = _direct("alice")
    store.write_tuples(
        Mutation(additions=frozenset({Tuple(subject=alice, relation="editor", object=document)}), deletions=frozenset())
    )
    evaluator = Evaluator(model=model, store=store)

    assert evaluator.check(alice, "viewer", document) is True
    assert evaluator.check(_direct("bob"), "viewer", document) is False


def test_union_short_circuits_right_branch() -> None:
    """
    Test that Union's right branch is never memoized when the left branch alone decides True.
    """
    model = _document_model()
    store = MemoryTupleStore()
    document = _document("42")
    alice = _direct("alice")
    store.write_tuples(
        Mutation(additions=frozenset({Tuple(subject=alice, relation="owner", object=document)}), deletions=frozenset())
    )
    evaluator = Evaluator(model=model, store=store)
    expression = Union(left=Reference(name="owner"), right=Reference(name="editor"))

    with store.snapshot() as view:
        context = EvaluationContext(view=view, budget=EvaluationBudget())
        result = evaluator._check_permission(alice, expression, document, context)

        assert result is True
        assert (document, "editor") not in context.memo


def test_check_permission_intersection_requires_both() -> None:
    """
    Test that Intersection is True only when both operands hold.
    """
    model = _document_model()
    store = MemoryTupleStore()
    document = _document("42")
    alice = _direct("alice")
    store.write_tuples(
        Mutation(additions=frozenset({Tuple(subject=alice, relation="owner", object=document)}), deletions=frozenset())
    )
    evaluator = Evaluator(model=model, store=store)

    assert evaluator.check(alice, "manager", document) is False

    store.write_tuples(
        Mutation(additions=frozenset({Tuple(subject=alice, relation="editor", object=document)}), deletions=frozenset())
    )
    assert evaluator.check(alice, "manager", document) is True


def test_exclusion_always_evaluates_both_sides() -> None:
    """
    Test that Exclusion evaluates both include and exclude, never short-circuiting either side.
    """
    model = _document_model()
    store = MemoryTupleStore()
    document = _document("42")
    alice = _direct("alice")
    evaluator = Evaluator(model=model, store=store)
    expression = Exclusion(include=Reference(name="owner"), exclude=Reference(name="blocked"))

    with store.snapshot() as view:
        context = EvaluationContext(view=view, budget=EvaluationBudget())
        result = evaluator._check_permission(alice, expression, document, context)

        assert result is False
        assert (document, "owner") in context.memo
        assert (document, "blocked") in context.memo


def test_exclusion_returns_true_when_only_include_holds() -> None:
    """
    Test that Exclusion allows when include holds and exclude does not — catches an include/exclude swap.

    If include/exclude were swapped internally, this asymmetric case
    (owner but not blocked) would incorrectly return False instead of
    True — same false-allow-class bug already caught for construction in
    test_operators.py.
    """
    model = _document_model()
    store = MemoryTupleStore()
    document = _document("42")
    alice = _direct("alice")
    store.write_tuples(
        Mutation(additions=frozenset({Tuple(subject=alice, relation="owner", object=document)}), deletions=frozenset())
    )
    evaluator = Evaluator(model=model, store=store)

    assert evaluator.check(alice, "restricted_viewer", document) is True


def test_exclusion_propagates_error_from_exclude_side() -> None:
    """
    Test that an EvaluationError raised while evaluating `exclude` propagates, never swallowed into False.

    docs/semantics.md: "an error on the exclude side must propagate even
    if include already evaluated to False" — a cycle reachable only
    through `exclude` must still surface.
    """
    model = CompiledModel(
        types={
            "document": Type(
                name="document",
                relations={"owner": Relation(allowed_subject_types=("user",))},
                permissions={
                    "cyclic": Reference(name="cyclic_alias"),
                    "cyclic_alias": Reference(name="cyclic"),
                    "restricted": Exclusion(include=Reference(name="owner"), exclude=Reference(name="cyclic")),
                },
            ),
        }
    )
    store = MemoryTupleStore()
    evaluator = Evaluator(model=model, store=store)

    with raises(EvaluationError):
        evaluator.check(_direct("alice"), "restricted", _document("42"))


def test_memoization_shared_across_relation_and_permission_paths() -> None:
    """
    Test that a second lookup of the same (object, name) hits the memo cache instead of recomputing.

    Exclusion never short-circuits (both sides always evaluate), so
    Exclusion(include=Reference("owner"), exclude=Reference("owner"))
    genuinely performs two lookups of (document, "owner") — unlike Union,
    where a True left branch would skip the right lookup entirely and
    never actually exercise the memo-hit path.
    """
    model = _document_model()
    store = MemoryTupleStore()
    document = _document("42")
    alice = _direct("alice")
    store.write_tuples(
        Mutation(additions=frozenset({Tuple(subject=alice, relation="owner", object=document)}), deletions=frozenset())
    )
    evaluator = Evaluator(model=model, store=store)
    expression = Exclusion(include=Reference(name="owner"), exclude=Reference(name="owner"))

    with store.snapshot() as view:
        context = EvaluationContext(view=view, budget=EvaluationBudget())
        result = evaluator._check_permission(alice, expression, document, context)

        assert result is False
        assert context.node_count == 1


def test_check_permission_unknown_expression_type_raises() -> None:
    """
    Test that an unrecognized PermissionExpression subtype raises EvaluationError (exhaustiveness fallback).
    """
    model = _document_model()
    store = MemoryTupleStore()
    document = _document("42")
    alice = _direct("alice")
    evaluator = Evaluator(model=model, store=store)

    with store.snapshot() as view:
        context = EvaluationContext(view=view, budget=EvaluationBudget())
        with raises(EvaluationError):
            evaluator._check_permission(alice, PermissionExpression(), document, context)


def _folder(id_: str) -> ObjectReference:
    return ObjectReference(type="folder", id=id_)


def _folder_model() -> CompiledModel:
    return CompiledModel(
        types={
            "folder": Type(
                name="folder",
                relations={
                    "viewer": Relation(allowed_subject_types=("user",)),
                    "parent": Relation(allowed_subject_types=("folder",)),
                },
                permissions={
                    "inherited_viewer": Union(
                        left=Reference(name="viewer"),
                        right=TupleToUserset(tupleset="parent", computed="inherited_viewer"),
                    ),
                },
            ),
        }
    )


def test_check_tuple_to_userset_traverses_parent() -> None:
    """
    Test that TupleToUserset follows the tupleset relation to a related object and checks computed there.
    """
    model = _folder_model()
    store = MemoryTupleStore()
    root = _folder("root")
    child = _folder("child")
    alice = _direct("alice")
    store.write_tuples(
        Mutation(
            additions=frozenset(
                {
                    Tuple(subject=DirectSubject(object=root), relation="parent", object=child),
                    Tuple(subject=alice, relation="viewer", object=root),
                }
            ),
            deletions=frozenset(),
        )
    )
    evaluator = Evaluator(model=model, store=store)

    assert evaluator.check(alice, "inherited_viewer", child) is True


def test_check_tuple_to_userset_ignores_subject_set_entries() -> None:
    """
    Test that a SubjectSet stored under the tupleset relation is skipped, not followed.
    """
    model = _folder_model()
    store = MemoryTupleStore()
    child = _folder("child")
    weird_group = SubjectSet(object=_folder("somewhere"), relation="viewer")
    store.write_tuples(
        Mutation(
            additions=frozenset({Tuple(subject=weird_group, relation="parent", object=child)}), deletions=frozenset()
        )
    )
    evaluator = Evaluator(model=model, store=store)

    assert evaluator.check(_direct("alice"), "inherited_viewer", child) is False


def test_check_tuple_to_userset_truncated_enumeration_raises() -> None:
    """
    Test that a truncated tupleset enumeration raises EvaluationError, not a silent False.

    max_nodes=4 is deliberate, not 1: the left Union branch (checking
    "viewer" directly on child, which has no tuples) already consumes 2
    nodes on its own — a tighter budget would raise from _check_name's
    own max_nodes guard before ever reaching _check_tuple_to_userset,
    testing the wrong code path. 4 leaves exactly 2 nodes of budget for
    the tupleset enumeration, which finds 3 parents and must truncate.
    """
    model = _folder_model()
    store = MemoryTupleStore()
    child = _folder("child")
    parents = [_folder(f"p{i}") for i in range(3)]
    store.write_tuples(
        Mutation(
            additions=frozenset(
                {Tuple(subject=DirectSubject(object=p), relation="parent", object=child) for p in parents}
            ),
            deletions=frozenset(),
        )
    )
    evaluator = Evaluator(model=model, store=store)

    with raises(EvaluationError):
        evaluator.check(_direct("alice"), "inherited_viewer", child, budget=EvaluationBudget(max_nodes=4))
