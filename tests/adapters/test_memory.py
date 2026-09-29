"""
Test module for the adapters/memory.py MemoryTupleStore.
"""

from os import environ
from pathlib import Path
from subprocess import run
from sys import executable
from tracemalloc import get_traced_memory, start, stop

from pytest import raises

from policy_pattern.adapters.memory import (
    MemoryTupleStore,
    _MemoryView,  # pyright: ignore[reportPrivateUsage]
)
from policy_pattern.models import DirectSubject, Mutation, ObjectReference, Tuple
from policy_pattern.ports import ReadResult


def _make_tuple(id_: str) -> Tuple:
    return Tuple(
        subject=DirectSubject(object=ObjectReference(type="user", id=id_)),
        relation="owner",
        object=ObjectReference(type="document", id="42"),
    )


def test_cannot_set_tuples_directly_into_memory_view() -> None:
    """
    Test that the _tuples attribute of a MemoryTupleStore is private and cannot be set directly.
    """
    memory_view = _MemoryView(frozenset({_make_tuple("alice")}))

    with raises(AttributeError):
        memory_view.tuples = frozenset()  # ty: ignore[invalid-assignment]


def test_read_after_write() -> None:
    """
    Test that a snapshot taken after write_tuples() observes the written tuple.
    """
    store = MemoryTupleStore()
    tuple_ = _make_tuple("alice")

    store.write_tuples(Mutation(additions=frozenset({tuple_}), deletions=frozenset()))

    with store.snapshot() as view:
        assert view.read_tuple(tuple_.subject, tuple_.relation, tuple_.object) is True


def test_read_relation_returns_complete_when_matches_at_or_under_limit() -> None:
    """
    Test that read_relation() reports complete=True when matches are within the limit.
    """
    store = MemoryTupleStore()
    tuples = frozenset({_make_tuple("alice"), _make_tuple("bob")})
    store.write_tuples(Mutation(additions=tuples, deletions=frozenset()))

    with store.snapshot() as view:
        result = view.read_relation(ObjectReference(type="document", id="42"), "owner", limit=2)

    assert result.complete is True
    assert result.tuples == tuples


def test_read_relation_truncates_exactly_at_limit() -> None:
    """
    Test that read_relation() reports complete=False and returns exactly `limit` tuples when more exist.
    """
    store = MemoryTupleStore()
    all_tuples = frozenset({_make_tuple(name) for name in ("alice", "bob", "carol")})
    store.write_tuples(Mutation(additions=all_tuples, deletions=frozenset()))

    with store.snapshot() as view:
        result = view.read_relation(ObjectReference(type="document", id="42"), "owner", limit=2)

    assert result.complete is False
    assert len(result.tuples) == 2


def test_read_relation_truncation_is_deterministic() -> None:
    """
    Test that truncation always keeps the same `limit` tuples, sorted by repr(), not an arbitrary subset.

    Guards against relying on frozenset iteration order (not stable across
    runs due to hash randomization), which would let which tuples survive
    truncation vary between runs with identical data.
    """
    store = MemoryTupleStore()
    all_tuples = frozenset({_make_tuple(name) for name in ("alice", "bob", "carol", "dave", "eve")})
    store.write_tuples(Mutation(additions=all_tuples, deletions=frozenset()))

    with store.snapshot() as view:
        result = view.read_relation(ObjectReference(type="document", id="42"), "owner", limit=3)

    expected = frozenset(sorted(all_tuples, key=repr)[:3])
    assert result.tuples == expected


def test_read_relation_with_limit_zero_reports_incomplete_when_matches_exist() -> None:
    """
    Test that limit=0 is well-defined: any match makes the result immediately incomplete, never a crash.
    """
    store = MemoryTupleStore()
    store.write_tuples(Mutation(additions=frozenset({_make_tuple("alice")}), deletions=frozenset()))

    with store.snapshot() as view:
        result = view.read_relation(ObjectReference(type="document", id="42"), "owner", limit=0)

    assert result == ReadResult(tuples=frozenset(), complete=False)


def test_read_relation_does_not_materialize_all_matches_before_truncating() -> None:
    """
    Test that read_relation() bounds peak memory to ~limit, not to the full match count.

    A naive `sorted(matching_candidates)` must fully materialize every
    match before truncating — with a huge match set and a small limit,
    that peaks at O(match count) instead of O(limit). This measures the
    actual allocation, not just the returned value (identical either way).
    Empirically: unfixed peaks at ~43MB for 200k matches; bounded to
    limit+1 peaks at a few KB. BLOCKER 3.
    """
    store = MemoryTupleStore()
    document_42 = ObjectReference(type="document", id="42")
    tuples = frozenset(
        Tuple(
            subject=DirectSubject(object=ObjectReference(type="user", id=f"user-{i}")),
            relation="owner",
            object=document_42,
        )
        for i in range(200_000)
    )
    store.write_tuples(Mutation(additions=tuples, deletions=frozenset()))

    with store.snapshot() as view:
        start()
        view.read_relation(document_42, "owner", limit=5)
        _, peak = get_traced_memory()
        stop()

    assert peak < 1_000_000, peak


_DETERMINISM_PROBE: Path = Path(__file__).parent / "determinism_probe.py"


def test_read_relation_truncation_is_deterministic_across_processes() -> None:
    """
    Test that read_relation() truncation is identical across different PYTHONHASHSEED values.

    frozenset iteration order depends on hash randomization, fixed once per
    process — a same-process test can pass by luck even against unsorted
    code (as observed: it did, once). Running the same query in separate
    subprocesses with different hash seeds is what actually proves the
    survivors don't depend on hash order.
    """
    outputs = {
        seed: run(  # noqa: S603 — the command and script path are fixed test data
            [executable, str(_DETERMINISM_PROBE)],
            env={**environ, "PYTHONHASHSEED": seed},
            capture_output=True,
            text=True,
            check=True,
            shell=False,
        ).stdout
        for seed in ("1", "42", "999")
    }

    assert len(set(outputs.values())) == 1, outputs
