"""Integration tests for the PostgreSQL TupleStore adapter."""

from collections.abc import Iterator
from typing import Any, cast

from psycopg_pool import ConnectionPool
from pytest import mark, raises

from policy_pattern.adapters.postgres import PostgresTupleStore, _PostgresView  # pyright: ignore[reportPrivateUsage]
from policy_pattern.evaluator import Evaluator
from policy_pattern.models import (
    CompiledModel,
    DirectSubject,
    Mutation,
    ObjectReference,
    Relation,
    SubjectSet,
    Tuple,
    Type,
)
from policy_pattern.ports import ReadResult


def _tuple(subject_id: str, *, object_id: str = "42", relation: str = "owner") -> Tuple:
    """
    Convenience function to create a Tuple with the given subject_id, object_id, and relation.
    """
    return Tuple(
        subject=DirectSubject(object=ObjectReference(type="user", id=subject_id)),
        relation=relation,
        object=ObjectReference(type="document", id=object_id),
    )


def _add(*tuples: Tuple) -> Mutation:
    """
    Convenience function to create a Mutation with the given tuples as additions and no deletions.
    """
    return Mutation(additions=frozenset(tuples), deletions=frozenset())


def _requests(
    store: PostgresTupleStore, subject: DirectSubject, first: ObjectReference, second: ObjectReference
) -> Iterator[tuple[DirectSubject, str, ObjectReference]]:
    """
    A generator that yields two requests, with a write in between.
    """
    yield (subject, "owner", first)
    store.write_tuples(_add(_tuple("alice", object_id="43")))
    yield (subject, "owner", second)


@mark.integration
@mark.slow
def test_write_tuples_inserts_one_row(
    postgres_pool: ConnectionPool,
) -> None:
    """Test that write_tuples() persists an inserted tuple."""
    tuple_ = _tuple("alice")

    PostgresTupleStore(cast(Any, postgres_pool)).write_tuples(_add(tuple_))

    with postgres_pool.connection() as connection, connection.cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM "authz_tuples"')
        assert cursor.fetchone() == (1,)


@mark.integration
@mark.slow
def test_duplicate_insertion_is_a_no_op(postgres_pool: ConnectionPool) -> None:
    """Test that inserting the same tuple twice leaves exactly one row."""
    store = PostgresTupleStore(cast(Any, postgres_pool))
    tuple_ = _tuple("alice")
    store.write_tuples(_add(tuple_))
    store.write_tuples(_add(tuple_))

    with store.snapshot() as view:
        assert view.read_tuple(tuple_.subject, tuple_.relation, tuple_.object) is True
        assert view.read_relation(tuple_.object, tuple_.relation, 10).tuples == frozenset({tuple_})


@mark.integration
@mark.slow
def test_additions_and_deletions_apply_together(postgres_pool: ConnectionPool) -> None:
    """Test that a mutation deletes and inserts its tuples in one call."""
    store = PostgresTupleStore(cast(Any, postgres_pool))
    old, new = _tuple("alice"), _tuple("bob")
    store.write_tuples(_add(old))
    store.write_tuples(Mutation(additions=frozenset({new}), deletions=frozenset({old})))

    with store.snapshot() as view:
        assert view.read_tuple(old.subject, old.relation, old.object) is False
        assert view.read_tuple(new.subject, new.relation, new.object) is True


@mark.integration
@mark.slow
def test_deletions_only_removes_tuple(postgres_pool: ConnectionPool) -> None:
    """Test that a deletion-only mutation removes its tuple."""
    store = PostgresTupleStore(cast(Any, postgres_pool))
    tuple_ = _tuple("alice")
    store.write_tuples(_add(tuple_))

    store.write_tuples(Mutation(additions=frozenset(), deletions=frozenset({tuple_})))

    with store.snapshot() as view:
        assert view.read_tuple(tuple_.subject, tuple_.relation, tuple_.object) is False


@mark.integration
@mark.slow
def test_empty_mutation_does_not_request_a_connection(postgres_pool: ConnectionPool) -> None:
    """Test that an empty mutation returns without making a pool request."""
    store = PostgresTupleStore(cast(Any, postgres_pool))
    requests_before = postgres_pool.get_stats()["requests_num"]
    store.write_tuples(Mutation(additions=frozenset(), deletions=frozenset()))
    assert postgres_pool.get_stats()["requests_num"] == requests_before


@mark.integration
@mark.slow
def test_snapshot_reads_after_write_and_checks_exact_fields(postgres_pool: ConnectionPool) -> None:
    """Test that snapshots see committed writes and read_tuple() requires an exact match."""
    store = PostgresTupleStore(cast(Any, postgres_pool))
    tuple_ = _tuple("alice")
    store.write_tuples(_add(tuple_))

    with store.snapshot() as view:
        assert view.read_tuple(tuple_.subject, tuple_.relation, tuple_.object) is True
        assert view.read_tuple(tuple_.subject, "viewer", tuple_.object) is False
        assert view.read_tuple(tuple_.subject, tuple_.relation, ObjectReference(type="document", id="43")) is False
        assert (
            view.read_tuple(
                DirectSubject(object=ObjectReference(type="user", id="bob")), tuple_.relation, tuple_.object
            )
            is False
        )


@mark.integration
@mark.slow
def test_snapshot_is_repeatable_read(postgres_pool: ConnectionPool) -> None:
    """Test that a snapshot cannot see a tuple committed after its first read."""
    store = PostgresTupleStore(cast(Any, postgres_pool))
    tuple_ = _tuple("alice")

    with store.snapshot() as view:
        assert view.read_tuple(tuple_.subject, tuple_.relation, tuple_.object) is False
        with postgres_pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO "authz_tuples" '
                    "(object_type, object_id, relation, subject_type, subject_id, subject_relation) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    ("document", "42", "owner", "user", "alice", ""),
                )
            connection.commit()
        assert view.read_tuple(tuple_.subject, tuple_.relation, tuple_.object) is False

    with store.snapshot() as next_view:
        assert next_view.read_tuple(tuple_.subject, tuple_.relation, tuple_.object) is True


@mark.integration
@mark.slow
def test_check_many_uses_one_postgres_snapshot_for_the_batch(postgres_pool: ConnectionPool) -> None:
    """Test that a tuple committed mid-batch is invisible to every request in that batch."""
    store = PostgresTupleStore(cast(Any, postgres_pool))
    evaluator = Evaluator(
        model=CompiledModel(
            types={
                "document": Type(
                    name="document",
                    relations={"owner": Relation(allowed_subject_types=("user",))},
                    permissions={},
                )
            }
        ),
        store=store,
    )
    subject = DirectSubject(object=ObjectReference(type="user", id="alice"))
    first = ObjectReference(type="document", id="42")
    second = ObjectReference(type="document", id="43")

    assert evaluator.check_many(cast(Any, _requests(store, subject, first, second))) == [False, False]
    assert evaluator.check(subject, "owner", second) is True


@mark.integration
@mark.slow
def test_read_relation_returns_complete_at_limit(postgres_pool: ConnectionPool) -> None:
    """Test that all matches at the limit are returned as complete."""
    store = PostgresTupleStore(cast(Any, postgres_pool))
    tuples = frozenset({_tuple("alice"), _tuple("bob")})
    store.write_tuples(_add(*tuples))

    with store.snapshot() as view:
        result = view.read_relation(ObjectReference(type="document", id="42"), "owner", limit=2)
    assert result == ReadResult(tuples=tuples, complete=True)


@mark.integration
@mark.slow
def test_read_relation_truncates_deterministically(postgres_pool: ConnectionPool) -> None:
    """Test that over-limit results contain exactly the limit and use stable ordering."""
    store = PostgresTupleStore(cast(Any, postgres_pool))
    tuples = frozenset({_tuple(name) for name in ("eve", "carol", "alice", "dave", "bob")})
    store.write_tuples(_add(*tuples))

    with store.snapshot() as view:
        first = view.read_relation(ObjectReference(type="document", id="42"), "owner", limit=3)
    with store.snapshot() as view:
        second = view.read_relation(ObjectReference(type="document", id="42"), "owner", limit=3)

    expected = frozenset(sorted(tuples, key=lambda item: item.subject.object.id)[:3])
    assert first == ReadResult(tuples=expected, complete=False)
    assert second == first


@mark.integration
@mark.slow
def test_read_relation_limit_zero_with_match_is_incomplete(postgres_pool: ConnectionPool) -> None:
    """Test that limit zero returns no tuples and reports truncation if a match exists."""
    store = PostgresTupleStore(cast(Any, postgres_pool))
    tuple_ = _tuple("alice")
    store.write_tuples(_add(tuple_))

    with store.snapshot() as view:
        result = view.read_relation(tuple_.object, tuple_.relation, limit=0)
    assert result == ReadResult(tuples=frozenset(), complete=False)


@mark.integration
@mark.slow
def test_read_relation_does_not_leak_across_objects(postgres_pool: ConnectionPool) -> None:
    """Test that a relation read only returns tuples for its requested object."""
    store = PostgresTupleStore(cast(Any, postgres_pool))
    requested, other = _tuple("alice", object_id="42"), _tuple("bob", object_id="43")
    store.write_tuples(_add(requested, other))

    with store.snapshot() as view:
        result = view.read_relation(requested.object, "owner", limit=10)
    assert result == ReadResult(tuples=frozenset({requested}), complete=True)


@mark.integration
@mark.slow
def test_subject_set_tuple_round_trips_through_database(postgres_pool: ConnectionPool) -> None:
    """Test that a subject set relation survives a write and read unchanged."""
    store = PostgresTupleStore(cast(Any, postgres_pool))
    tuple_ = Tuple(
        subject=SubjectSet(object=ObjectReference(type="group", id="engineering"), relation="member"),
        relation="viewer",
        object=ObjectReference(type="document", id="42"),
    )
    store.write_tuples(_add(tuple_))

    with store.snapshot() as view:
        assert view.read_tuple(tuple_.subject, tuple_.relation, tuple_.object) is True
        result = view.read_relation(tuple_.object, tuple_.relation, limit=10)
    assert result == ReadResult(tuples=frozenset({tuple_}), complete=True)


@mark.unit
def test_cannot_set_connection_directly_into_postgres_view() -> None:
    """
    Test that the _connection attribute of a _PostgresView is private and cannot be set directly.
    """
    postgres_view: _PostgresView = _PostgresView(connection=cast(Any, None))

    with raises(AttributeError):
        postgres_view.connection = True  # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[invalid-assignment]
