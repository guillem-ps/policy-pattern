"""
Fixtures for PostgreSQL adapter integration tests.
"""

from collections.abc import Iterator
from importlib.resources import files
from os import environ
from typing import LiteralString, cast

from psycopg import Connection
from psycopg.rows import TupleRow
from psycopg.sql import SQL
from psycopg_pool import ConnectionPool
from pytest import fixture
from testcontainers.community.postgres import PostgresContainer

# NOTE: Override for testing propose
# TEST_POSTGRES_IMAGE=postgres:17-alpine uv run pytest -m integration
POSTGRES_IMAGE: str = environ.get("TEST_POSTGRES_IMAGE", "postgres:16-alpine")


@fixture(scope="session")
def postgres_container() -> Iterator[PostgresContainer]:
    """Provide a PostgreSQL 16 container for adapter integration tests."""
    with PostgresContainer(POSTGRES_IMAGE, driver=None) as container:
        yield container


@fixture
def postgres_pool(
    postgres_container: PostgresContainer,
) -> Iterator[ConnectionPool[Connection[TupleRow]]]:
    """Provide a pool with the schema installed and an empty table."""
    pool: ConnectionPool[Connection[TupleRow]] = ConnectionPool(
        conninfo=postgres_container.get_connection_url(),
        open=False,
    )

    try:
        pool.open(wait=True)

        migration: str = (
            files("policy_pattern")
            .joinpath("sql", "postgres", "0001_create_policy_tuples.sql")
            .read_text(encoding="utf-8")
        )

        with pool.connection() as connection, connection.cursor() as cursor:
            cursor.execute(SQL(cast(LiteralString, migration)))
            cursor.execute('TRUNCATE TABLE "authz_tuples"')  # Ensure the table is empty before each test run

        yield pool
    finally:
        pool.close()
