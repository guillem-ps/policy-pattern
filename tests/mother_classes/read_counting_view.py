"""
A View wrapper that counts every read_tuple()/read_relation() call issued through it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from policy_pattern.models import (
    ObjectReference,
    Subject,
)
from policy_pattern.ports import ReadResult, View

if TYPE_CHECKING:
    from .read_counting_store import ReadCountingStore


class ReadCountingView(View):
    """
    A View wrapper that counts every read_tuple()/read_relation() call issued through it.
    """

    def __init__(self, inner: View, store: ReadCountingStore) -> None:
        """
        Constructs a ReadCountingView that wraps an inner View and a ReadCountingStore to keep track of read counts.
        """
        self._inner = inner
        self._store = store

    @override
    def read_tuple(self, subject: Subject, relation: str, object: ObjectReference) -> bool:
        """
        Read a tuple from the inner view and increment the read count in the associated ReadCountingStore.
        """
        self._store.read_count += 1
        return self._inner.read_tuple(subject, relation, object)

    @override
    def read_relation(self, object: ObjectReference, relation: str, limit: int) -> ReadResult:
        """
        Read a relation from the inner view and increment the read count in the associated ReadCountingStore.
        """
        self._store.read_count += 1
        return self._inner.read_relation(object, relation, limit)
