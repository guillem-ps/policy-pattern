"""
Test the SnapshotCountingStore class, which is a
wrapper around a TupleStore that counts how many times snapshot() is called.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import override

from policy_pattern.models import (
    Mutation,
)
from policy_pattern.ports import TupleStore, View


class SnapshotCountingStore(TupleStore):
    """
    A TupleStore wrapper that counts how many times snapshot() is called.
    """

    def __init__(self, inner: TupleStore) -> None:
        """
        Initializes the wrapper with an inner TupleStore and sets the snapshot count to zero.
        """
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
