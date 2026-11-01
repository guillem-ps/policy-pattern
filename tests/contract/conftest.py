"""Shared fixtures for the TupleStore contract suite."""

from collections.abc import Iterator

from pytest import FixtureRequest, fixture, mark, param

from policy_pattern.adapters.memory import MemoryTupleStore
from policy_pattern.adapters.postgres import PostgresTupleStore
from policy_pattern.ports import TupleStore


@fixture(params=["memory", param("postgres", marks=mark.integration)])
def store(request: FixtureRequest) -> Iterator[TupleStore]:
    """Run contract tests against memory and real PostgreSQL stores."""
    if request.param == "postgres":
        postgres_pool = request.getfixturevalue("postgres_pool")
        yield PostgresTupleStore(postgres_pool)
    else:
        yield MemoryTupleStore()
