"""
A TupleStore wrapper that counts every read_tuple()/read_relation() call
issued through its snapshot's View, across the view's whole lifetime.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import override

from policy_pattern.models import (
    Mutation,
)
from policy_pattern.ports import TupleStore, View

from .read_counting_view import ReadCountingView


class ReadCountingStore(TupleStore):
    """
    A TupleStore wrapper that counts every read_tuple()/read_relation() call
    issued through its snapshot's View, across the view's whole lifetime.
    """

    def __init__(self, inner: TupleStore) -> None:
        """
        Constructs a ReadCountingStore that wraps an inner TupleStore and initializes the read count to zero.
        """
        self._inner = inner
        self.read_count = 0

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
        Open a snapshot of the inner store and yield a ReadCountingView that wraps the inner view and this store.
        """
        with self._inner.snapshot() as view:
            yield ReadCountingView(view, self)
