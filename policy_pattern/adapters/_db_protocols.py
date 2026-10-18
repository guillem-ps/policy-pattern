"""
Common interface shapes for DB-API 2.0 (https://peps.python.org/pep-0249/) connections, cursors, and connection pools.
"""

from abc import abstractmethod
from collections.abc import Sequence
from contextlib import AbstractContextManager
from typing import Any, Protocol


class Cursor(Protocol):
    """
    Structural shape of a DB-API 2.0 cursor — satisfied by psycopg's real Cursor, with no import or inheritance.
    """

    @abstractmethod
    def execute(self, query: str, params: Sequence[Any] = ()) -> object:
        """
        Executes a SQL statement with optional parameters.
        """
        raise NotImplementedError

    @abstractmethod
    def executemany(self, query: str, params_seq: Sequence[Sequence[Any]]) -> None:
        """
        Executes the same SQL statement for each sequence of parameters in the sequence.
        """
        raise NotImplementedError

    @abstractmethod
    def fetchone(self) -> tuple[Any, ...] | None:
        """
        Fetches the next row of a query result, returning a single tuple, or None when
        no more rows are available.
        """
        raise NotImplementedError

    @abstractmethod
    def fetchall(self) -> list[tuple[Any, ...]]:
        """
        Fetches all remaining rows of a query result, returning a list of tuples.
        """
        raise NotImplementedError


class Connection(Protocol):
    """
    Structural shape of a DB-API 2.0 connection.

    Deliberately plain commit()/rollback(), not psycopg3's own
    transaction() context-manager convenience — that sugar is
    psycopg3-specific and would narrow this Protocol to one driver.
    """

    @abstractmethod
    def cursor(self) -> Cursor:
        """
        Returns a new Cursor object using the connection.
        """
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> None:
        """
        Commits the current transaction.
        """
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        """
        Rolls back the current transaction.
        """
        raise NotImplementedError


class ConnectionPool(Protocol):
    """
    Structural shape of a connection pool — satisfied by psycopg_pool.ConnectionPool, with no import.
    """

    @abstractmethod
    def connection(self) -> AbstractContextManager[Connection]:
        """
        Returns a context manager that yields a Connection from the pool.

        returns:
            An AbstractContextManager that yields a Connection object.
        """
        raise NotImplementedError
