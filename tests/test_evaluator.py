"""
Test module for evaluator.py.
"""

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import FrozenInstanceError
from os import environ
from pathlib import Path
from subprocess import run
from sys import executable
from typing import override

from pytest import mark, raises

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
    Subject,
    SubjectSet,
    Tuple,
    TupleToUserset,
    Type,
    Union,
)
from policy_pattern.ports import ReadResult, TupleStore, View


def _chain(prefix: str, length: int) -> list[ObjectReference]:
    """
    Create a chain of ObjectReferences with IDs prefixed by `prefix` and numbered from 0 to `length - 1`.
    """
    return [_group(f"{prefix}{i}") for i in range(length)]


@mark.unit
def test_evaluation_budget_default_values() -> None:
    """
    Test that EvaluationBudget uses the documented defaults when constructed with no arguments.
    """
    budget = EvaluationBudget()
    assert budget.max_depth == 25
    assert budget.max_nodes == 10_000
    assert budget.max_store_reads == 1_000


@mark.unit
def test_evaluation_budget_equality() -> None:
    """
    Test that two EvaluationBudget instances with the same field values are equal.
    """
    assert EvaluationBudget(max_depth=5, max_nodes=10, max_store_reads=20) == EvaluationBudget(
        max_depth=5, max_nodes=10, max_store_reads=20
    )


@mark.unit
def test_evaluation_budget_inequality_different_max_depth() -> None:
    """
    Test that two EvaluationBudget instances with a different max_depth are not equal.
    """
    assert EvaluationBudget(max_depth=5) != EvaluationBudget(max_depth=6)


@mark.unit
def test_evaluation_budget_hash_consistency() -> None:
    """
    Test that equal EvaluationBudget instances have the same hash value.
    """
    assert hash(EvaluationBudget(max_depth=5)) == hash(EvaluationBudget(max_depth=5))


@mark.unit
def test_evaluation_budget_is_frozen() -> None:
    """
    Test that EvaluationBudget instances cannot be mutated after construction.
    """
    budget = EvaluationBudget()

    with raises(FrozenInstanceError):
        budget.max_depth = 1  # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[invalid-assignment]

    with raises(FrozenInstanceError):
        budget.max_nodes = 1  # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[invalid-assignment]

    with raises(FrozenInstanceError):
        budget.max_store_reads = 1  # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[invalid-assignment]


@mark.unit
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


@mark.unit
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
    """
    Create a DirectSubject for the given user ID.
    """
    return DirectSubject(object=ObjectReference(type="user", id=id_))


def _group(id_: str) -> ObjectReference:
    """
    Create an ObjectReference for a group with the given ID.
    """
    return ObjectReference(type="group", id=id_)


def _group_model() -> CompiledModel:
    """
    Create a CompiledModel with a single group type.
    The group type has a "member" relation that allows subjects of type "user" or "group#member".
    """
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
    """
    A TupleStore wrapper that counts how many times snapshot() is called.
    """

    def __init__(self, inner: TupleStore) -> None:
        self._inner = inner
        self.snapshot_count = 0

    @override
    def write_tuples(self, mutation: Mutation) -> None:
        """
        Write tuples to the inner store.
        """
        self._inner.write_tuples(mutation)

    @override
    @contextmanager
    def snapshot(self) -> Generator[View, None, None]:
        """
        Open a snapshot of the inner store and increment the snapshot count.
        """
        self.snapshot_count += 1
        with self._inner.snapshot() as view:
            yield view


class _ReadCountingStore(TupleStore):
    """
    A TupleStore wrapper that counts every read_tuple()/read_relation() call
    issued through its snapshot's View, across the view's whole lifetime.
    """

    def __init__(self, inner: TupleStore) -> None:
        self._inner = inner
        self.read_count = 0

    @override
    def write_tuples(self, mutation: Mutation) -> None:
        self._inner.write_tuples(mutation)

    @override
    @contextmanager
    def snapshot(self) -> Generator[View, None, None]:
        with self._inner.snapshot() as view:
            yield _ReadCountingView(view, self)


class _ReadCountingView(View):
    def __init__(self, inner: View, store: "_ReadCountingStore") -> None:
        self._inner = inner
        self._store = store

    @override
    def read_tuple(self, subject: Subject, relation: str, object: ObjectReference) -> bool:
        self._store.read_count += 1
        return self._inner.read_tuple(subject, relation, object)

    @override
    def read_relation(self, object: ObjectReference, relation: str, limit: int) -> ReadResult:
        self._store.read_count += 1
        return self._inner.read_relation(object, relation, limit)


@mark.unit
def test_check_many_shares_memo_across_requests() -> None:
    """
    Test that a sub-check shared by several requests is paid for once,
    counted directly rather than inferred from a budget threshold — a
    budget-based assertion is unsound here: a fresh per-request context
    also resets the budget counter, so no error fires either way and the
    decisions come out identical regardless of memo sharing.
    """
    model = CompiledModel(
        types={
            "folder": Type(
                name="folder", relations={"viewer": Relation(allowed_subject_types=("user",))}, permissions={}
            ),
            "document": Type(
                name="document",
                relations={"parent": Relation(allowed_subject_types=("folder",))},
                permissions={"can_view": TupleToUserset(tupleset="parent", computed="viewer")},
            ),
        }
    )
    inner = MemoryTupleStore()
    root = _folder("root")
    docs = [ObjectReference(type="document", id=str(i)) for i in range(3)]
    alice = _direct("alice")
    additions = {Tuple(subject=alice, relation="viewer", object=root)}
    for d in docs:
        additions.add(Tuple(subject=DirectSubject(object=root), relation="parent", object=d))
    inner.write_tuples(Mutation(additions=frozenset(additions), deletions=frozenset()))
    store = _ReadCountingStore(inner)
    evaluator = Evaluator(model=model, store=store)

    requests = [(alice, "can_view", d) for d in docs]

    assert evaluator.check_many(requests) == [True, True, True]
    assert store.read_count == 4


@mark.unit
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


@mark.unit
def test_check_direct_relation_no_match() -> None:
    """
    Test that check() returns False when no tuple and no userset expansion matches.
    """
    model = _group_model()
    store = MemoryTupleStore()
    evaluator = Evaluator(model=model, store=store)

    assert evaluator.check(_direct("alice"), "member", _group("a")) is False


@mark.unit
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


@mark.unit
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


@mark.unit
def test_check_relation_ignores_tuple_with_disallowed_subject_type() -> None:
    """
    Test that check() never counts a stored tuple whose subject type isn't in Relation.allowed_subject_types.

    group:a#member only allows ("user", "group#member") — a tuple whose
    subject is itself a bare group (DirectSubject of type "group", not a
    SubjectSet) is malformed data that should never have been written;
    check() must not treat it as proof of membership. BLOCKER 1.
    """
    model = _group_model()
    store = MemoryTupleStore()
    group_a = _group("a")
    rogue_subject = DirectSubject(object=_group("rogue"))
    store.write_tuples(
        Mutation(
            additions=frozenset({Tuple(subject=rogue_subject, relation="member", object=group_a)}),
            deletions=frozenset(),
        )
    )
    evaluator = Evaluator(model=model, store=store)

    assert evaluator.check(rogue_subject, "member", group_a) is False


@mark.unit
def test_check_relation_ignores_userset_expansion_with_disallowed_shape() -> None:
    """
    Test that check() never follows a SubjectSet whose "type#relation" shape isn't in allowed_subject_types.

    document:42#owner only allows ("user",) — no userset form declared.
    A tuple document:42#owner@group:eng#member is malformed; even though
    alice is a real member of group:eng, check() must not use that path
    to grant owner. BLOCKER 1.
    """
    model = CompiledModel(
        types={
            "document": Type(
                name="document", relations={"owner": Relation(allowed_subject_types=("user",))}, permissions={}
            ),
            "group": Type(
                name="group", relations={"member": Relation(allowed_subject_types=("user",))}, permissions={}
            ),
        }
    )
    store = MemoryTupleStore()
    alice = _direct("alice")
    group_eng = ObjectReference(type="group", id="eng")
    document_42 = ObjectReference(type="document", id="42")
    store.write_tuples(
        Mutation(
            additions=frozenset(
                {
                    Tuple(
                        subject=SubjectSet(object=group_eng, relation="member"), relation="owner", object=document_42
                    ),
                    Tuple(subject=alice, relation="member", object=group_eng),
                }
            ),
            deletions=frozenset(),
        )
    )
    evaluator = Evaluator(model=model, store=store)

    assert evaluator.check(alice, "owner", document_42) is False


@mark.unit
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


_EVALUATOR_DETERMINISM_PROBE: Path = Path(__file__).parent / "evaluator_determinism_probe.py"


@mark.unit
def test_check_relation_userset_expansion_order_is_deterministic_across_processes() -> None:
    """
    Test that check()'s userset-expansion order (and thus its verdict) is stable across PYTHONHASHSEED values.

    group:a#member has two SubjectSet branches: one cycles straight back
    to (group:a, "member") itself, the other resolves cleanly to True via
    group:c. Which branch any() visits first decides whether check()
    returns True or raises EvaluationError — before the fix that was
    frozenset iteration order (hash-seed dependent, proven empirically:
    varies across PYTHONHASHSEED); after the fix it must be a canonical
    repr-sorted order, identical in every process. BLOCKER 2.
    """
    outputs = {
        seed: run(  # noqa: S603 — the command and script path are fixed test data
            [executable, str(_EVALUATOR_DETERMINISM_PROBE)],
            env={**environ, "PYTHONHASHSEED": seed},
            capture_output=True,
            text=True,
            check=True,
            shell=False,
        ).stdout
        for seed in ("1", "2", "3", "42", "999")
    }

    assert len(set(outputs.values())) == 1, outputs


def _chain_of_groups(length: int) -> list[ObjectReference]:
    return [_group(str(i)) for i in range(length)]


@mark.unit
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


@mark.unit
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


@mark.unit
def test_check_many_max_depth_resets_between_requests() -> None:
    """
    Test that max_depth bounds each request's own traversal, not the batch:
    two independent chains each exactly at the depth limit both succeed in
    one batch — if max_depth accumulated like max_nodes/max_store_reads,
    the second request would exceed it and raise.
    """
    model = _group_model()
    store = MemoryTupleStore()
    alice = _direct("alice")

    chain_a = _chain("a", 2)
    chain_b = _chain("b", 2)

    additions: set[Tuple] = set()

    for chain in (chain_a, chain_b):
        additions.add(Tuple(subject=SubjectSet(object=chain[1], relation="member"), relation="member", object=chain[0]))
        additions.add(Tuple(subject=alice, relation="member", object=chain[1]))

    store.write_tuples(Mutation(additions=frozenset(additions), deletions=frozenset()))
    evaluator = Evaluator(model=model, store=store)

    requests = [(alice, "member", chain_a[0]), (alice, "member", chain_b[0])]
    assert evaluator.check_many(requests, budget=EvaluationBudget(max_depth=2)) == [True, True]


@mark.unit
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


@mark.unit
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


@mark.unit
def test_check_degenerate_budget_raises_evaluation_error_not_something_else() -> None:
    """
    Test that a degenerate EvaluationBudget (max_nodes=0) fails cleanly with EvaluationError.
    """
    model = _group_model()
    store = MemoryTupleStore()
    evaluator = Evaluator(model=model, store=store)

    with raises(EvaluationError):
        evaluator.check(_direct("alice"), "member", _group("a"), budget=EvaluationBudget(max_nodes=0))


@mark.unit
def test_check_raises_unknown_type_error_for_undeclared_object_type() -> None:
    """
    Test that check() raises UnknownTypeError when object.type is not declared in the CompiledModel.
    """
    model = _group_model()
    store = MemoryTupleStore()
    evaluator = Evaluator(model=model, store=store)

    with raises(UnknownTypeError):
        evaluator.check(_direct("alice"), "member", ObjectReference(type="document", id="42"))


@mark.unit
def test_check_raises_unknown_type_error_via_userset_expansion() -> None:
    """
    Test that userset expansion into a SubjectSet with an undeclared object.type raises UnknownTypeError.

    "document#member" must be an allowed shape on this relation — otherwise
    the BLOCKER 1 shape guard filters the tuple out before ever reaching
    the type lookup this test exists to exercise, and "document" itself is
    still never declared as an actual Type in this model.
    """
    model = CompiledModel(
        types={
            "group": Type(
                name="group",
                relations={"member": Relation(allowed_subject_types=("user", "group#member", "document#member"))},
                permissions={},
            ),
        }
    )
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


@mark.unit
def test_check_raises_unknown_name_error_for_undeclared_name() -> None:
    """
    Test that check() raises UnknownNameError (not a raw KeyError) for a name declared nowhere on the type.
    """
    model = _group_model()
    store = MemoryTupleStore()
    evaluator = Evaluator(model=model, store=store)

    with raises(UnknownNameError):
        evaluator.check(_direct("alice"), "not_a_real_relation_or_permission", _group("a"))


@mark.unit
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
    """
    Return a CompiledModel with a "document" type that has "owner", "editor",
    and "blocked" relations, and "viewer", "manager", and "restricted_viewer"
    permissions.
    """
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


@mark.unit
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


@mark.unit
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


@mark.unit
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
        result = evaluator._check_permission(alice, expression, document, context)  # pyright: ignore[reportPrivateUsage]

        assert result is True
        assert (alice, document, "editor") not in context.memo


@mark.unit
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


@mark.unit
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
        result = evaluator._check_permission(alice, expression, document, context)  # pyright: ignore[reportPrivateUsage]

        assert result is False
        assert (alice, document, "owner") in context.memo
        assert (alice, document, "blocked") in context.memo


@mark.unit
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


@mark.unit
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


@mark.unit
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
        result = evaluator._check_permission(alice, expression, document, context)  # pyright: ignore[reportPrivateUsage]

        assert result is False
        assert context.node_count == 1


@mark.unit
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
        with raises(EvaluationError) as exc_info:
            evaluator._check_permission(alice, PermissionExpression(), document, context)  # pyright: ignore[reportPrivateUsage]

    assert exc_info.value.message == "unknown expression type 'PermissionExpression'"


def _folder(id_: str) -> ObjectReference:
    """
    Return an ObjectReference of type "folder" with the given id.
    """
    return ObjectReference(type="folder", id=id_)


def _folder_model() -> CompiledModel:
    """
    Return a CompiledModel with a "folder" type that has a "viewer" relation and an "inherited_viewer" permission that
    uses TupleToUserset to inherit viewers from its parent folder.
    """
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


@mark.unit
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


@mark.unit
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


@mark.unit
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


@mark.unit
def test_memo_is_not_shared_across_subjects() -> None:
    """
    Test that one EvaluationContext reused for two different subjects gives each its own decision.

    The memo key is what this pins down. Keyed by `(object, name)` alone it
    is safe only because a single `check()` call carries exactly one
    subject, constant for the whole traversal — an invariant `check_many()`
    is about to break by design. With the narrow key, alice's cached True
    for `(document:42, "owner")` is handed straight back to bob, who owns
    nothing: a false allow, the worst failure class this library has.

    Reusing one context across two `_check_name` calls is exactly what a
    batch does, which is why this reproduces the bug without `check_many()`
    existing yet.
    """
    model = _document_model()
    store = MemoryTupleStore()
    document = _document("42")
    alice = _direct("alice")
    bob = _direct("bob")

    store.write_tuples(
        Mutation(additions=frozenset({Tuple(subject=alice, relation="owner", object=document)}), deletions=frozenset())
    )
    evaluator = Evaluator(model=model, store=store)

    with store.snapshot() as view:
        context = EvaluationContext(view=view, budget=EvaluationBudget())

        assert evaluator._check_name(alice, "owner", document, context) is True  # pyright: ignore[reportPrivateUsage]
        assert evaluator._check_name(bob, "owner", document, context) is False  # pyright: ignore[reportPrivateUsage]


@mark.unit
def test_check_many_different_subjects_do_not_share_memo() -> None:
    """
    Test that two different subjects checking the same (object, name) in one
    batch each get their own correct answer, not a cached answer meant for
    the other subject — the false-allow-class bug Task 1's key widening
    exists to prevent.
    """
    model = _document_model()
    store = MemoryTupleStore()
    document = _document("42")
    alice = _direct("alice")
    bob = _direct("bob")
    store.write_tuples(
        Mutation(additions=frozenset({Tuple(subject=alice, relation="owner", object=document)}), deletions=frozenset())
    )
    evaluator = Evaluator(model=model, store=store)

    results = evaluator.check_many([(alice, "viewer", document), (bob, "viewer", document)])

    assert results == [True, False]


@mark.unit
def test_check_many_preserves_order_and_duplicates() -> None:
    """
    Test that check_many() returns one bool per request, in input order,
    including a repeated request.
    """
    model = _document_model()
    store = MemoryTupleStore()
    document = _document("42")
    alice = _direct("alice")
    store.write_tuples(
        Mutation(additions=frozenset({Tuple(subject=alice, relation="owner", object=document)}), deletions=frozenset())
    )
    evaluator = Evaluator(model=model, store=store)
    requests = [
        (alice, "viewer", document),
        (_direct("bob"), "viewer", document),
        (alice, "viewer", document),
    ]

    assert evaluator.check_many(requests) == [True, False, True]


@mark.unit
def test_check_many_budget_shared_across_requests() -> None:
    """
    Test that the budget's counters accumulate across the whole batch —
    enough distinct, cheap requests still exhaust a small shared
    max_store_reads, proving the budget isn't reissued per request.
    """
    model = _document_model()
    store = MemoryTupleStore()
    alice = _direct("alice")
    for doc_id in ("1", "2", "3"):
        store.write_tuples(
            Mutation(
                additions=frozenset({Tuple(subject=alice, relation="owner", object=_document(doc_id))}),
                deletions=frozenset(),
            )
        )
    evaluator = Evaluator(model=model, store=store)
    requests = [(alice, "owner", _document(doc_id)) for doc_id in ("1", "2", "3")]

    with raises(EvaluationError):
        evaluator.check_many(requests, budget=EvaluationBudget(max_store_reads=2))


@mark.unit
def test_check_many_propagates_error_and_returns_nothing() -> None:
    """
    Test that an error on any request aborts check_many() entirely instead
    of returning a partial list or swallowing the exception.
    """
    model = _document_model()
    store = MemoryTupleStore()
    alice = _direct("alice")
    evaluator = Evaluator(model=model, store=store)
    requests = [
        (alice, "viewer", _document("42")),
        (alice, "viewer", ObjectReference(type="nonexistent", id="1")),
    ]

    with raises(UnknownTypeError):
        evaluator.check_many(requests)


@mark.unit
def test_check_many_empty_requests_returns_empty_list() -> None:
    """
    Test that check_many([]) returns [] without raising.
    """
    model = _document_model()
    store = MemoryTupleStore()
    evaluator = Evaluator(model=model, store=store)

    assert evaluator.check_many([]) == []


@mark.unit
def test_check_many_opens_exactly_one_snapshot() -> None:
    """
    Test that a whole batch runs inside a single store.snapshot().

    docs/semantics.md's snapshot-consistency requirement is per `check()`;
    `check_many()` extends it to the batch, so a three-request batch must
    not see three different views of the store. Counting snapshots is the
    only observation that catches a per-request `snapshot()` — the
    decisions themselves come out identical either way.
    """
    model = _document_model()
    inner = MemoryTupleStore()
    alice = _direct("alice")
    for doc_id in ("1", "2", "3"):
        inner.write_tuples(
            Mutation(
                additions=frozenset({Tuple(subject=alice, relation="owner", object=_document(doc_id))}),
                deletions=frozenset(),
            )
        )
    store = _SnapshotCountingStore(inner)
    evaluator = Evaluator(model=model, store=store)

    evaluator.check_many([(alice, "owner", _document(doc_id)) for doc_id in ("1", "2", "3")])

    assert store.snapshot_count == 1
