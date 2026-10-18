"""
PostgreSQL TupleStore adapter — typed against a stdlib Protocol, no database driver import.
"""

from collections.abc import Generator
from contextlib import contextmanager
from importlib.resources import files
from typing import Any, override

from policy_pattern.models import Mutation, ObjectReference, Subject
from policy_pattern.ports import ReadResult, TupleStore, View

from ._db_protocols import Connection, ConnectionPool, Cursor
from ._tuple_mapping import columns, compose, decompose

MIGRATION_RESOURCE: tuple[str, str, str] = ("sql", "postgres", "0001_create_policy_tuples.sql")

_INSERT_SQL: str = """
    INSERT INTO "authz_tuples"
    (object_type, object_id, relation, subject_type, subject_id, subject_relation)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (object_type, object_id, relation, subject_type, subject_id, subject_relation)
    DO NOTHING
    """

_DELETE_SQL: str = """
    DELETE FROM "authz_tuples"
    WHERE object_type=%s AND object_id=%s AND relation=%s
    AND subject_type=%s AND subject_id=%s AND subject_relation=%s
    """

_READ_TUPLE_SQL: str = """
    SELECT 1 FROM "authz_tuples"
    WHERE object_type=%s AND object_id=%s AND relation=%s
    AND subject_type=%s AND subject_id=%s AND subject_relation=%s
    """

_READ_RELATION_SQL: str = """
    SELECT subject_type, subject_id, subject_relation FROM "authz_tuples"
    WHERE object_type=%s AND object_id=%s AND relation=%s
    ORDER BY subject_type, subject_id, subject_relation LIMIT %s
    """


class PostgresTupleStore(TupleStore):
    """
    PostgreSQL-backed TupleStore — typed against a structural Protocol, no database driver import.

    Stores tuples in the fixed table `authz_tuples`. The matching schema ships as a versioned SQL
    resource (`policy_pattern/sql/postgres/0001_create_policy_tuples.sql`)
    for the consuming service's own migration tooling to apply — this
    adapter never creates or migrates schema itself, unless `auto_create_schema=True`.

    Precondition (documented, not runtime-checked): every connection
    `pool` hands out must have `autocommit=False` (DB-API 2.0's own
    required default). If violated, write_tuples() loses atomicity and
    snapshot()'s isolation-level statement has no transaction to apply to.

    `auto_create_schema` (default False): when True, runs the packaged
    migration (`CREATE TABLE IF NOT EXISTS`) once at construction time,
    using a connection from `pool`. Requires that connection's role to
    have `CREATE` privilege — stricter than the default
    (`SELECT`/`INSERT`/`DELETE` only). Not a substitute for a real
    migration history: concurrent process startup may run this
    concurrently across instances — Postgres serializes the DDL
    internally so this does not corrupt the schema, but it is not
    tracked by any migration tool either. See `docs/usage/README.md`
    for when this trade-off is worth taking.
    """

    def __init__(self, pool: ConnectionPool, *, auto_create_schema: bool = False) -> None:
        """
        Stores the pool for later use. Never opens a connection or touches the
        database, unless `auto_create_schema=True`.
        """
        self._pool = pool
        if auto_create_schema:
            self._create_schema()

    def _create_schema(self) -> None:
        """
        Applies the packaged migration directly. Only reachable when
        `auto_create_schema=True` — never part of the default construction path.

        try/except/rollback, same reason as write_tuples(): the pool's
        connection() context manager does not roll back on its own, so a
        failed execute() would otherwise return an aborted transaction to
        the pool for the next caller to trip over.
        """
        migration_sql = files("policy_pattern").joinpath(*MIGRATION_RESOURCE).read_text(encoding="utf-8")
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(migration_sql)
            except Exception:
                conn.rollback()
                raise
            else:
                conn.commit()

    @override
    def write_tuples(self, mutation: Mutation) -> None:
        """
        Atomically applies additions/deletions; commit() is the visibility point.

        Empty mutations short-circuit before acquiring a connection. Uses
        cursor()/commit()/rollback() explicitly — plain DB-API 2.0, not
        psycopg3's own transaction() convenience, so this stays portable
        to any driver satisfying Connection.
        """
        if not mutation.additions and not mutation.deletions:
            return
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            try:
                if mutation.deletions:
                    cursor.executemany(_DELETE_SQL, [columns(t) for t in mutation.deletions])
                if mutation.additions:
                    cursor.executemany(_INSERT_SQL, [columns(t) for t in mutation.additions])
            except Exception:
                conn.rollback()
                raise
            else:
                conn.commit()

    @override
    @contextmanager
    def snapshot(self) -> Generator[View, None, None]:
        """
        Opens a REPEATABLE READ, READ ONLY transaction held for the view's lifetime.

        SET TRANSACTION, not a literal BEGIN — with autocommit=False (the
        documented pool precondition), psycopg already opens a
        transaction implicitly before the first statement on a fresh
        connection; a literal BEGIN here would be a redundant, nested
        BEGIN, which Postgres warns about and simply ignores outright —
        its isolation-level clause never runs, leaving the already-open
        transaction at the default READ COMMITTED. SET TRANSACTION sets
        the characteristics of the already-open transaction directly
        instead, which Postgres requires as the first statement inside
        it — satisfied here since this is literally the first
        cursor.execute() call after checkout. The pool's own
        connection() context manager returns the connection to the pool
        on __exit__ regardless of exception; the inner try/finally
        guarantees rollback() runs on both normal completion and an
        exception raised while the view is open.
        """
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            try:
                yield _PostgresView(conn)
            finally:
                conn.rollback()


class _PostgresView(View):
    """
    Read-only view over one REPEATABLE READ Postgres transaction.

    Private: nothing outside PostgresTupleStore.snapshot() ever
    constructs one directly — same convention as _MemoryView.
    """

    def __init__(self, connection: Connection) -> None:
        """
        Wraps the already-open, already-in-transaction connection.
        """
        self._connection = connection

    @property
    def connection(self) -> Connection:
        """
        Returns the already-open, already-in-transaction connection.

        Private: nothing outside PostgresTupleStore.snapshot() ever
        needs to see this.
        """
        return self._connection

    @override
    def read_tuple(self, subject: Subject, relation: str, object: ObjectReference) -> bool:
        """
        Returns whether the exact tuple `(subject, relation, object)` exists in this view.
        """
        subject_type, subject_id, subject_relation = decompose(subject)
        cursor: Cursor = self.connection.cursor()

        cursor.execute(
            _READ_TUPLE_SQL,
            (object.type, object.id, relation, subject_type, subject_id, subject_relation),
        )

        return cursor.fetchone() is not None

    @override
    def read_relation(self, object: ObjectReference, relation: str, limit: int) -> ReadResult:
        """
        Returns up to `limit` tuples matching the given object and relation, in a single query.
        """
        cursor: Cursor = self.connection.cursor()
        cursor.execute(
            _READ_RELATION_SQL,
            (object.type, object.id, relation, limit + 1),
        )

        rows: list[tuple[Any, ...]] = cursor.fetchall()
        tuples = frozenset(compose(r, relation, object) for r in rows[:limit])

        return ReadResult(tuples=tuples, complete=len(rows) <= limit)
