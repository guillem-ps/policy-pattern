"""
In-memory TupleStore adapter — demo/test adapter, no throughput requirement.
"""

from collections.abc import Generator
from contextlib import contextmanager
from threading import Lock
from typing import override

from policy_pattern.models import Mutation, ObjectReference, Subject, Tuple
from policy_pattern.ports import ReadResult, TupleStore, View


class MemoryTupleStore(TupleStore):
    """
    In-memory `TupleStore` — a plain `set[Tuple]` behind a lock, no index.

    `read_relation()` does a linear scan over a snapshot; no
    `dict[(object, relation), set[Tuple]]` index is maintained. An index
    would need to stay in lockstep with `write_tuples()` on every call —
    real complexity bought for a performance property this adapter is
    explicitly not required to have (`docs/semantics.md` § Threading calls
    it a "demo/test adapter with no throughput requirement"). Real
    throughput is `PostgresTupleStore`'s job, not this one's.

    Example:
        store = MemoryTupleStore()
        store.write_tuples(Mutation(additions=frozenset({t}), deletions=frozenset()))
        with store.snapshot() as view:
            view.read_tuple(subject, "owner", object)
    """

    def __init__(self) -> None:
        """
        Starts empty.
        """
        self._tuples: set[Tuple] = set()
        self._lock = Lock()

    @override
    def write_tuples(self, mutation: Mutation) -> None:
        """
        Atomically applies additions/deletions under the lock.

        `Mutation.__post_init__` already guarantees `additions`/`deletions`
        are disjoint — this method does not re-validate that.
        """
        with self._lock:
            self._tuples = (self._tuples - mutation.deletions) | mutation.additions

    @override
    @contextmanager
    def snapshot(self) -> Generator[View, None, None]:
        """
        Copies the current tuple set under the lock, then yields a view over the copy.

        The copy — not a re-held lock — is what makes the view stable: once
        the copy exists, nothing that happens to the live set afterward can
        be observed through the already-open view, because the view never
        looks at the live set again.
        """
        with self._lock:
            frozen = frozenset(self._tuples)
        yield _MemoryView(frozen)


class _MemoryView(View):
    """
    Read-only view over one immutable snapshot of a `MemoryTupleStore`.

    Private: nothing outside `MemoryTupleStore.snapshot()` ever constructs
    one directly.
    """

    def __init__(self, tuples: frozenset[Tuple]) -> None:
        """
        Wraps an already-copied, immutable tuple set.
        """
        self._tuples = tuples

    @property
    def tuples(self) -> frozenset[Tuple]:
        """
        Returns the snapshot's tuples.

        Private: nothing outside `MemoryTupleStore.snapshot()` ever needs
        to see this.
        """
        return self._tuples

    @override
    def read_tuple(self, subject: Subject, relation: str, object: ObjectReference) -> bool:
        """
        Checks exact membership by constructing the equivalent Tuple.

        Reuses `Tuple.__post_init__`'s own validation (delegating `relation`
        to `Identifier`) instead of duplicating it here.
        """
        return Tuple(subject=subject, relation=relation, object=object) in self.tuples

    @override
    def read_relation(self, object: ObjectReference, relation: str, limit: int) -> ReadResult:
        """
        Linearly scans the snapshot for matches, bounded by `limit + 1`.

        Args:
            object: The `ObjectReference` to match.
            relation: The relation name to match.
            limit: The maximum number of matches to return. If more than
                `limit` matches exist, the result is truncated to exactly
                `limit` and `complete=False`.

        Matches are sorted by `repr()` before truncating — `frozenset`
        iteration order is not stable (hash randomization), and an
        unordered scan would make which tuples survive truncation vary
        between runs with identical data, breaking
        docs/architecture.md's determinism guarantee. `limit=0` needs no
        special-casing: it is already well-defined (immediately
        incomplete if any match exists, complete-and-empty otherwise).
        """
        candidates: list[Tuple] = sorted(
            (t for t in self.tuples if t.object == object and t.relation == relation),
            key=repr,
        )

        if len(candidates) > limit:
            return ReadResult(tuples=frozenset(candidates[:limit]), complete=False)

        return ReadResult(tuples=frozenset(candidates), complete=True)
