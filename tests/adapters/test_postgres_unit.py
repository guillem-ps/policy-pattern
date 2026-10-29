"""Unit tests for PostgreSQL adapter behavior that does not require a database."""

from collections.abc import Generator, Sequence
from contextlib import AbstractContextManager, contextmanager
from importlib.resources import files
from typing import Any, override

from pytest import mark, raises

from policy_pattern.adapters._db_protocols import Connection, ConnectionPool, Cursor
from policy_pattern.adapters.postgres import PostgresTupleStore
from policy_pattern.errors import IndexEntryTooLargeError
from policy_pattern.models import DirectSubject, Mutation, ObjectReference, Tuple


class _CursorDouble(Cursor):
    """Cursor double with safe no-op defaults — subclasses override only what they test."""

    @override
    def execute(self, query: str, params: Sequence[Any] = ()) -> object:
        return None

    @override
    def executemany(self, query: str, params_seq: Sequence[Sequence[Any]]) -> None:
        return None

    @override
    def fetchone(self) -> tuple[Any, ...] | None:
        return None

    @override
    def fetchall(self) -> list[tuple[Any, ...]]:
        return []


class _FailingCursor(_CursorDouble):
    """Cursor double that raises on every batch execution."""

    @override
    def executemany(self, query: str, params_seq: Sequence[Sequence[Any]]) -> None:
        raise RuntimeError("deliberate executemany failure")


class _PartiallyFailingCursor(_CursorDouble):
    """Cursor double whose first batch execution succeeds and second one raises.

    write_tuples() issues deletions' executemany() first, then additions'
    — this double lets a test prove the whole batch rolls back together
    even when only the *second* call fails, not just when the first one
    does.
    """

    def __init__(self) -> None:
        self.executemany_calls = 0

    @override
    def executemany(self, query: str, params_seq: Sequence[Sequence[Any]]) -> None:
        self.executemany_calls += 1
        if self.executemany_calls == 2:
            raise RuntimeError("deliberate second-batch failure")


class _RecordingCursor(_CursorDouble):
    """Cursor double that records every execute() call's SQL text."""

    def __init__(self) -> None:
        self.executed: list[str] = []

    @override
    def execute(self, query: str, params: Sequence[Any] = ()) -> object:
        self.executed.append(query)
        return None


class _FailingExecuteCursor(_CursorDouble):
    """Cursor double that raises on execute() — unlike _FailingCursor, which raises on executemany()."""

    @override
    def execute(self, query: str, params: Sequence[Any] = ()) -> object:
        raise RuntimeError("deliberate execute failure")


class _ConnectionDouble(Connection):
    """Connection double that records transaction finalization calls."""

    def __init__(self, cursor_double: Cursor) -> None:
        self.rollback_calls = 0
        self.commit_calls = 0
        self.cursor_double = cursor_double

    @override
    def cursor(self) -> Cursor:
        return self.cursor_double

    @override
    def commit(self) -> None:
        self.commit_calls += 1

    @override
    def rollback(self) -> None:
        self.rollback_calls += 1


class _PoolDouble(ConnectionPool):
    """Pool double that yields one connection double."""

    def __init__(self, connection: Connection) -> None:
        self.connection_double = connection

    @override
    @contextmanager
    def connection(self) -> Generator[Connection, None, None]:
        yield self.connection_double


class _NeverCalledPool(ConnectionPool):
    """Pool double whose connection() always fails — proves a code path never reaches it."""

    @override
    def connection(self) -> AbstractContextManager[Connection]:
        raise AssertionError("pool.connection() must not be called when auto_create_schema is False")


@mark.unit
def test_write_tuples_rolls_back_and_reraises_executemany_error() -> None:
    """Test that a batch write failure rolls back once and preserves its exception."""
    connection = _ConnectionDouble(_FailingCursor())
    pool = _PoolDouble(connection)
    tuple_ = Tuple(
        subject=DirectSubject(object=ObjectReference(type="user", id="alice")),
        relation="owner",
        object=ObjectReference(type="document", id="42"),
    )
    mutation = Mutation(additions=frozenset({tuple_}), deletions=frozenset())

    with raises(RuntimeError, match="^deliberate executemany failure$"):
        PostgresTupleStore(pool).write_tuples(mutation)

    assert connection.rollback_calls == 1
    assert connection.commit_calls == 0


@mark.unit
def test_write_tuples_rejects_an_addition_whose_key_exceeds_the_btree_index_limit() -> None:
    """Test that an addition whose encoded primary key would exceed Postgres's B-tree index entry
    limit is rejected before any connection is acquired, instead of reaching the driver as a raw
    "index row size exceeds btree ... maximum" error.

    `four_byte_char * 255` is Identifier's own max length (255 code points), each one a 4-byte
    UTF-8 character (U+10348, outside the BMP) — a value that is perfectly valid per Identifier's
    own contract. Three such columns alone already sum past Postgres's ~2704-byte limit for the
    default 8KB page size, without needing to max out all six.
    """
    four_byte_char = "\U00010348"
    huge = four_byte_char * 255
    tuple_ = Tuple(
        subject=DirectSubject(object=ObjectReference(type="user", id=huge)),
        relation=huge,
        object=ObjectReference(type=huge, id="42"),
    )
    mutation = Mutation(additions=frozenset({tuple_}), deletions=frozenset())

    with raises(IndexEntryTooLargeError):
        PostgresTupleStore(_NeverCalledPool()).write_tuples(mutation)


@mark.unit
def test_auto_create_schema_rolls_back_and_reraises_on_error() -> None:
    """Test that a failed CREATE TABLE rolls back instead of returning an aborted transaction to the pool."""
    connection = _ConnectionDouble(_FailingExecuteCursor())
    pool = _PoolDouble(connection)

    with raises(RuntimeError, match="^deliberate execute failure$"):
        PostgresTupleStore(pool, auto_create_schema=True)

    assert connection.rollback_calls == 1
    assert connection.commit_calls == 0


@mark.unit
def test_auto_create_schema_runs_packaged_migration_once() -> None:
    """Test that auto_create_schema=True executes the packaged DDL and commits before any other use."""
    cursor = _RecordingCursor()
    connection = _ConnectionDouble(cursor)
    pool = _PoolDouble(connection)

    PostgresTupleStore(pool, auto_create_schema=True)

    expected_sql = files("policy_pattern").joinpath("sql", "postgres", "0001_create_policy_tuples.sql").read_text()
    assert len(cursor.executed) == 1
    assert cursor.executed[0] == expected_sql
    assert connection.commit_calls == 1


@mark.unit
def test_auto_create_schema_defaults_to_false_and_touches_nothing() -> None:
    """Test that omitting auto_create_schema never calls the pool at construction time."""
    PostgresTupleStore(_NeverCalledPool())


@mark.unit
def test_write_tuples_rolls_back_deletions_when_additions_fail() -> None:
    """Test that a mutation's deletions roll back together with a later failure on its additions.

    write_tuples() runs deletions' executemany() before additions' — this
    proves the two share one transaction: a failure on the *second* call
    still undoes the first, rather than leaving the deletion committed on
    its own.
    """
    connection = _ConnectionDouble(_PartiallyFailingCursor())
    pool = _PoolDouble(connection)
    old = Tuple(
        subject=DirectSubject(object=ObjectReference(type="user", id="alice")),
        relation="owner",
        object=ObjectReference(type="document", id="42"),
    )
    new = Tuple(
        subject=DirectSubject(object=ObjectReference(type="user", id="bob")),
        relation="owner",
        object=ObjectReference(type="document", id="42"),
    )
    mutation = Mutation(additions=frozenset({new}), deletions=frozenset({old}))

    with raises(RuntimeError, match="^deliberate second-batch failure$"):
        PostgresTupleStore(pool).write_tuples(mutation)

    assert connection.rollback_calls == 1
    assert connection.commit_calls == 0
