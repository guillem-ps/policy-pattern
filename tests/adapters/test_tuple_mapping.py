"""Unit tests for PostgreSQL tuple column mapping."""

from pytest import mark

from policy_pattern.adapters._tuple_mapping import columns, compose, decompose
from policy_pattern.models import DirectSubject, ObjectReference, SubjectSet, Tuple


def _direct_tuple() -> Tuple:
    return Tuple(
        subject=DirectSubject(object=ObjectReference(type="user", id="alice")),
        relation="owner",
        object=ObjectReference(type="document", id="42"),
    )


def _subject_set_tuple() -> Tuple:
    return Tuple(
        subject=SubjectSet(object=ObjectReference(type="group", id="engineering"), relation="member"),
        relation="viewer",
        object=ObjectReference(type="document", id="42"),
    )


@mark.unit
def test_columns_decomposes_direct_subject() -> None:
    """Test that columns() encodes a direct subject with an empty relation."""
    assert columns(_direct_tuple()) == ("document", "42", "owner", "user", "alice", "")


@mark.unit
def test_columns_decomposes_subject_set() -> None:
    """Test that columns() preserves a subject set relation."""
    assert columns(_subject_set_tuple()) == ("document", "42", "viewer", "group", "engineering", "member")


@mark.unit
def test_decompose_handles_direct_subject() -> None:
    """Test that decompose() encodes direct subjects with an empty relation."""
    assert decompose(_direct_tuple().subject) == ("user", "alice", "")


@mark.unit
def test_decompose_handles_subject_set() -> None:
    """Test that decompose() preserves subject set relations."""
    assert decompose(_subject_set_tuple().subject) == ("group", "engineering", "member")


@mark.unit
def test_compose_reconstructs_direct_subject() -> None:
    """Test that compose() reconstructs the direct subject branch."""
    tuple_ = _direct_tuple()
    assert compose(("user", "alice", ""), tuple_.relation, tuple_.object) == tuple_


@mark.unit
def test_compose_reconstructs_subject_set() -> None:
    """Test that compose() reconstructs the subject set branch."""
    tuple_ = _subject_set_tuple()
    assert compose(("group", "engineering", "member"), tuple_.relation, tuple_.object) == tuple_


@mark.unit
def test_columns_then_compose_round_trips_tuple() -> None:
    """Test that mapping a tuple to columns and back preserves its value."""
    for tuple_ in (_direct_tuple(), _subject_set_tuple()):
        object_ = ObjectReference(type=tuple_.object.type, id=tuple_.object.id)
        assert compose(columns(tuple_)[3:], tuple_.relation, object_) == tuple_
