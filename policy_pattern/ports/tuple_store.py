"""
Storage port: TupleStore/View abstractions and the bounded-read result type.
"""

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from dataclasses import dataclass

from ..models import Mutation, ObjectReference, Subject, Tuple


@dataclass(frozen=True, slots=True)
class ReadResult:
    """
    Result of a bounded `View.read_relation()` call.

    `docs/semantics.md` requires that a truncated enumeration never be
    representable as a complete one — `complete` carries that fact in the
    type itself rather than a convention the caller has to already know
    (e.g. a `limit + 1` sentinel). `tuples` is a `frozenset` — it carries no
    order of its own. When more matching tuples exist than the caller's
    `limit` allowed, `tuples` holds at most `limit` of them, deterministically
    selected by the adapter's own canonical ranking (never arbitrary or
    hash-order-dependent — see `MemoryTupleStore.read_relation`), and
    `complete` is `False`; otherwise `tuples` holds all matches and
    `complete` is `True`.

    Example:
        ReadResult(tuples=frozenset({...}), complete=True)
    """

    tuples: frozenset[Tuple]
    complete: bool


class TupleStore(ABC):
    """
    Storage port for authorization tuples — mutations plus consistent-snapshot reads.

    Deliberately schema-agnostic: this class stores and compares
    structurally well-formed `(subject, relation, object)` triples and
    knows nothing about `Relation` vs `Permission`, rewrite rules, or
    `compile()` — that separation is what keeps a `PostgresTupleStore`
    substitutable for `MemoryTupleStore` without either one leaking into
    the rewrite engine (`docs/architecture.md`).

    `write_tuples()` is the only mutating method an adapter must implement.
    `delete_tuples()` is concrete, not abstract — a pure deletion is already
    representable as `Mutation(additions=frozenset(), deletions=tuples)`,
    so every adapter gets deletion for free instead of reimplementing the
    same atomicity/disjointness guarantees `write_tuples()` already provides.

    Example:
        store.write_tuples(Mutation(additions=frozenset({t}), deletions=frozenset()))
        store.delete_tuples(frozenset({t}))
    """

    @abstractmethod
    def write_tuples(self, mutation: Mutation) -> None:
        """
        Atomically applies a mutation's additions and deletions.

        See `docs/semantics.md` § Write mutations for the full contract
        (atomicity, idempotency, visibility point) — this method's
        implementation must satisfy it, this docstring does not restate it.
        """
        raise NotImplementedError

    def delete_tuples(self, tuples: frozenset[Tuple]) -> None:
        """
        Deletes the given tuples atomically, as a deletion-only Mutation.
        """
        self.write_tuples(Mutation(additions=frozenset(), deletions=tuples))

    @abstractmethod
    def snapshot(self) -> AbstractContextManager["View"]:
        """
        Opens an evaluation-scoped, read-only view pinned to one consistent snapshot.

        See `docs/semantics.md` § Snapshot consistency of check() — every
        read issued through the same `View` must observe the same logical
        store state for the view's whole lifetime.
        """
        raise NotImplementedError


class View(ABC):
    """
    Read-only handle pinned to one consistent snapshot of a `TupleStore`.

    No write method exists here at all — `docs/semantics.md` already
    decided mutations are issued against `TupleStore` itself, never through
    a view; this class makes that an actual absence of a method, not just a
    sentence in a doc.

    Example:
        with store.snapshot() as view:
            view.read_tuple(subject, "owner", object)
            view.read_relation(object, "owner", limit=100)
    """

    @abstractmethod
    def read_tuple(self, subject: Subject, relation: str, object: ObjectReference) -> bool:
        """
        Returns whether the exact tuple `(subject, relation, object)` exists in this view.
        """
        raise NotImplementedError

    @abstractmethod
    def read_relation(self, object: ObjectReference, relation: str, limit: int) -> ReadResult:
        """
        Enumerates subjects/usersets holding `relation` on `object`, bounded by `limit`.

        See `ReadResult`'s docstring for what `complete=False` means and
        when it is set. An adapter must not materialize more than
        `limit + 1` matching tuples before returning — that would violate the contract.
        """
        raise NotImplementedError

    @abstractmethod
    def read_tuples_for_subject(self, subject: Subject, limit: int) -> ReadResult:
        """
        Enumerates every tuple whose subject exactly matches `subject`, bounded by `limit`.

        Unlike `read_relation`, this is not filtered by relation name or
        object; callers needing narrower results filter returned tuples.
        See `ReadResult` for the `complete=False` contract.
        """
        raise NotImplementedError
