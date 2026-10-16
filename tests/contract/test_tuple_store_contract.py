"""
Shared TupleStore contract suite — runs against every adapter.

A passing suite here is what AGENTS.md calls out as the actual proof of
substitutability; a single-adapter suite proves nothing.
"""

from collections.abc import Iterator

from pytest import FixtureRequest, fixture, mark, param

from policy_pattern.adapters.memory import MemoryTupleStore
from policy_pattern.adapters.postgres import PostgresTupleStore
from policy_pattern.models import DirectSubject, Mutation, ObjectReference, SubjectSet, Tuple
from policy_pattern.ports import ReadResult, TupleStore


def _make_direct_tuple(subject_id: str) -> Tuple:
    return Tuple(
        subject=DirectSubject(object=ObjectReference(type="user", id=subject_id)),
        relation="owner",
        object=ObjectReference(type="document", id="42"),
    )


def _make_subject_set_tuple() -> Tuple:
    return Tuple(
        subject=SubjectSet(object=ObjectReference(type="group", id="eng"), relation="member"),
        relation="editor",
        object=ObjectReference(type="document", id="42"),
    )


@fixture(params=["memory", param("postgres", marks=mark.integration)])
def store(request: FixtureRequest) -> Iterator[TupleStore]:
    """
    Parametrized fixture — every test in this module runs once per adapter.

    The "postgres" parametrization carries its own `integration` marker
    via `pytest.param(..., marks=...)`, so `pytest -m "not integration"`
    excludes it directly — no collection hook needed. `postgres_pool` is
    still requested lazily via `request.getfixturevalue`, not as a direct
    fixture parameter, so the "memory" parametrization never spins up a
    container.
    """
    if request.param == "postgres":
        postgres_pool = request.getfixturevalue("postgres_pool")
        yield PostgresTupleStore(postgres_pool)
    else:
        yield MemoryTupleStore()


@mark.contract
def test_read_after_write(store: TupleStore) -> None:
    """
    Test that a snapshot taken after write_tuples() observes the written tuple.
    """
    tuple_ = _make_direct_tuple("alice")
    store.write_tuples(Mutation(additions=frozenset({tuple_}), deletions=frozenset()))

    with store.snapshot() as view:
        assert view.read_tuple(tuple_.subject, tuple_.relation, tuple_.object) is True


@mark.contract
def test_read_after_write_with_subject_set(store: TupleStore) -> None:
    """
    Test read-after-write for a SubjectSet-shaped tuple, not only DirectSubject.
    """
    tuple_ = _make_subject_set_tuple()
    store.write_tuples(Mutation(additions=frozenset({tuple_}), deletions=frozenset()))

    with store.snapshot() as view:
        assert view.read_tuple(tuple_.subject, tuple_.relation, tuple_.object) is True
        result = view.read_relation(tuple_.object, tuple_.relation, limit=10)
    assert result.tuples == frozenset({tuple_})


@mark.contract
def test_write_idempotency(store: TupleStore) -> None:
    """
    Test that writing an existing tuple again is a no-op.
    """
    tuple_ = _make_direct_tuple("alice")
    store.write_tuples(Mutation(additions=frozenset({tuple_}), deletions=frozenset()))
    store.write_tuples(Mutation(additions=frozenset({tuple_}), deletions=frozenset()))

    with store.snapshot() as view:
        result = view.read_relation(ObjectReference(type="document", id="42"), "owner", limit=10)
    assert result.tuples == frozenset({tuple_})


@mark.contract
def test_delete_idempotency(store: TupleStore) -> None:
    """
    Test that deleting a nonexistent tuple is a no-op that succeeds.
    """
    store.delete_tuples(frozenset({_make_direct_tuple("ghost")}))


@mark.contract
def test_delete_tuples_removes_a_written_tuple(store: TupleStore) -> None:
    """
    Test that delete_tuples() actually removes a previously written tuple.
    """
    tuple_ = _make_direct_tuple("alice")
    store.write_tuples(Mutation(additions=frozenset({tuple_}), deletions=frozenset()))

    store.delete_tuples(frozenset({tuple_}))

    with store.snapshot() as view:
        assert view.read_tuple(tuple_.subject, tuple_.relation, tuple_.object) is False


@mark.contract
def test_truncation_is_exact_at_the_boundary(store: TupleStore) -> None:
    """
    Test that exactly `limit` matches is complete=True, and `limit + 1` is complete=False with `limit` tuples.
    """
    tuples = frozenset({_make_direct_tuple("alice"), _make_direct_tuple("bob")})
    store.write_tuples(Mutation(additions=tuples, deletions=frozenset()))

    with store.snapshot() as view:
        exact = view.read_relation(ObjectReference(type="document", id="42"), "owner", limit=2)
    assert exact.complete is True

    store.write_tuples(Mutation(additions=frozenset({_make_direct_tuple("carol")}), deletions=frozenset()))

    with store.snapshot() as view:
        truncated = view.read_relation(ObjectReference(type="document", id="42"), "owner", limit=2)
    assert truncated.complete is False
    assert len(truncated.tuples) == 2


@mark.contract
def test_limit_zero_is_well_defined(store: TupleStore) -> None:
    """
    Test that limit=0 with an existing match returns an empty, incomplete result — never raises.
    """
    store.write_tuples(Mutation(additions=frozenset({_make_direct_tuple("alice")}), deletions=frozenset()))

    with store.snapshot() as view:
        result = view.read_relation(ObjectReference(type="document", id="42"), "owner", limit=0)

    assert result == ReadResult(tuples=frozenset(), complete=False)


@mark.contract
def test_mutation_additions_and_deletions_apply_together(store: TupleStore) -> None:
    """
    Test that one mutation's additions and deletions both take effect.
    """
    alice, bob = _make_direct_tuple("alice"), _make_direct_tuple("bob")
    store.write_tuples(Mutation(additions=frozenset({alice}), deletions=frozenset()))

    store.write_tuples(Mutation(additions=frozenset({bob}), deletions=frozenset({alice})))

    with store.snapshot() as view:
        result = view.read_relation(ObjectReference(type="document", id="42"), "owner", limit=10)
    assert result.tuples == frozenset({bob})


@mark.contract
def test_empty_mutation_is_a_no_op(store: TupleStore) -> None:
    """
    Test that an empty mutation does not raise and changes nothing.
    """
    store.write_tuples(Mutation(additions=frozenset(), deletions=frozenset()))

    with store.snapshot() as view:
        result = view.read_relation(ObjectReference(type="document", id="42"), "owner", limit=10)
    assert result == ReadResult(tuples=frozenset(), complete=True)


@mark.contract
def test_snapshot_does_not_see_a_write_issued_after_it_opened(store: TupleStore) -> None:
    """
    Test that an already-open view never observes a write issued after its snapshot was taken.

    This is docs/semantics.md's evaluation-scoped view guarantee — the
    actual property that must hold identically across every adapter, not
    just the one most likely to get it wrong (Postgres, via a concurrent
    connection). `MemoryTupleStore` must prove it too: its snapshot is a
    copy taken at open time, so a write that happens afterward, through
    the same `store` reference, must stay invisible to the already-open
    view just the same.
    """
    tuple_ = _make_direct_tuple("alice")

    with store.snapshot() as view:
        assert view.read_tuple(tuple_.subject, tuple_.relation, tuple_.object) is False

        store.write_tuples(Mutation(additions=frozenset({tuple_}), deletions=frozenset()))

        assert view.read_tuple(tuple_.subject, tuple_.relation, tuple_.object) is False

    with store.snapshot() as next_view:
        assert next_view.read_tuple(tuple_.subject, tuple_.relation, tuple_.object) is True
