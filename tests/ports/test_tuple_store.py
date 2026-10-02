"""
Test module for the ports/tuple_store.py port surface.
"""

from dataclasses import FrozenInstanceError

from pytest import raises

from policy_pattern.models import DirectSubject, Mutation, ObjectReference, Tuple
from policy_pattern.ports.tuple_store import ReadResult, TupleStore, View

from ..mother_classes import MotherTupleStore


def _make_tuple(id_: str) -> Tuple:
    return Tuple(
        subject=DirectSubject(object=ObjectReference(type="user", id=id_)),
        relation="owner",
        object=ObjectReference(type="document", id="42"),
    )


def test_read_result_valid_construction() -> None:
    """
    Test that a valid ReadResult can be constructed without raising an error.
    """
    tuples = frozenset({_make_tuple("alice")})
    result = ReadResult(tuples=tuples, complete=True)
    assert result.tuples == tuples
    assert result.complete is True


def test_read_result_equality() -> None:
    """
    Test that two ReadResult instances with the same fields are equal.
    """
    tuples = frozenset({_make_tuple("alice")})
    assert ReadResult(tuples=tuples, complete=True) == ReadResult(tuples=tuples, complete=True)


def test_read_result_inequality_different_tuples() -> None:
    """
    Test that two ReadResult instances with different tuples are not equal.
    """
    assert ReadResult(tuples=frozenset({_make_tuple("alice")}), complete=True) != ReadResult(
        tuples=frozenset({_make_tuple("bob")}), complete=True
    )


def test_read_result_inequality_different_complete() -> None:
    """
    Test that two ReadResult instances with a different complete flag are not equal.
    """
    tuples = frozenset({_make_tuple("alice")})
    assert ReadResult(tuples=tuples, complete=True) != ReadResult(tuples=tuples, complete=False)


def test_read_result_hash_consistency() -> None:
    """
    Test that equal ReadResult instances have the same hash value.
    """
    tuples = frozenset({_make_tuple("alice")})
    assert hash(ReadResult(tuples=tuples, complete=True)) == hash(ReadResult(tuples=tuples, complete=True))


def test_read_result_is_frozen() -> None:
    """
    Test that ReadResult instances cannot be mutated after construction.
    """
    result = ReadResult(tuples=frozenset(), complete=True)

    with raises(FrozenInstanceError):
        result.tuples = frozenset()  # ty: ignore[invalid-assignment]

    with raises(FrozenInstanceError):
        result.complete = False  # ty: ignore[invalid-assignment]


def test_tuple_store_cannot_be_instantiated_directly() -> None:
    """
    Test that TupleStore cannot be instantiated directly — it is an ABC.
    """
    with raises(TypeError):
        TupleStore()


def test_view_cannot_be_instantiated_directly() -> None:
    """
    Test that View cannot be instantiated directly — it is an ABC.
    """
    with raises(TypeError):
        View()


def test_delete_tuples_calls_write_tuples_with_deletion_only_mutation() -> None:
    """
    Test that delete_tuples() delegates to write_tuples() with a deletion-only Mutation.

    TupleStore only declares write_tuples() as abstract — delete_tuples() is
    a concrete method every adapter gets for free, built on top of it.
    """
    store = MotherTupleStore()
    tuple_ = _make_tuple("alice")

    store.delete_tuples(frozenset({tuple_}))

    assert store.received_mutation == Mutation(additions=frozenset(), deletions=frozenset({tuple_}))


def test_snapshot_is_usable_as_a_context_manager() -> None:
    """
    Test that snapshot() returns something usable in a `with` block, yielding a View.
    """
    store = MotherTupleStore()

    with store.snapshot() as view:
        assert isinstance(view, View)
