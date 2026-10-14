"""Unit tests for PostgreSQL adapter behavior that does not require a database."""

from collections.abc import Generator, Sequence
from contextlib import contextmanager
from typing import Any, cast

from pytest import mark, raises

from policy_pattern.adapters.postgres import PostgresTupleStore
from policy_pattern.models import DirectSubject, Mutation, ObjectReference, Tuple


class _FailingCursor:
    """Cursor double that raises on every batch execution."""

    def execute(self, query: str, params: Sequence[Any] = ()) -> object:
        return None

    def executemany(self, query: str, params_seq: Sequence[Sequence[Any]]) -> None:
        raise RuntimeError("deliberate executemany failure")

    def fetchone(self) -> tuple[Any, ...] | None:
        return None

    def fetchall(self) -> list[tuple[Any, ...]]:
        return []


class _PartiallyFailingCursor:
    """Cursor double whose first batch execution succeeds and second one raises.

    write_tuples() issues deletions' executemany() first, then additions'
    — this double lets a test prove the whole batch rolls back together
    even when only the *second* call fails, not just when the first one
    does.
    """

    def __init__(self) -> None:
        self.executemany_calls = 0

    def execute(self, query: str, params: Sequence[Any] = ()) -> object:
        return None

    def executemany(self, query: str, params_seq: Sequence[Sequence[Any]]) -> None:
        self.executemany_calls += 1
        if self.executemany_calls == 2:
            raise RuntimeError("deliberate second-batch failure")

    def fetchone(self) -> tuple[Any, ...] | None:
        return None

    def fetchall(self) -> list[tuple[Any, ...]]:
        return []


class _ConnectionDouble:
    """Connection double that records transaction finalization calls."""

    def __init__(self, cursor_double: _FailingCursor | _PartiallyFailingCursor) -> None:
        self.rollback_calls = 0
        self.commit_calls = 0
        self.cursor_double = cursor_double

    def cursor(self) -> _FailingCursor | _PartiallyFailingCursor:
        return self.cursor_double

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1


class _PoolDouble:
    """Pool double that yields one connection double."""

    def __init__(self, connection: _ConnectionDouble) -> None:
        self.connection_double = connection

    @contextmanager
    def connection(self) -> Generator[_ConnectionDouble, None, None]:
        yield self.connection_double


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
        PostgresTupleStore(cast(Any, pool)).write_tuples(mutation)

    assert connection.rollback_calls == 1
    assert connection.commit_calls == 0


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
        PostgresTupleStore(cast(Any, pool)).write_tuples(mutation)

    assert connection.rollback_calls == 1
    assert connection.commit_calls == 0
