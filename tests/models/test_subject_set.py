"""
Test module for the SubjectSet class.
"""

from dataclasses import FrozenInstanceError

from pytest import mark, raises

from policy_pattern.errors import InvalidIdentifierError
from policy_pattern.models import ObjectReference, SubjectSet


@mark.unit
def test_subject_set_valid_construction() -> None:
    """
    Test that a valid SubjectSet can be constructed without raising an error.
    """
    subject_set = SubjectSet(object=ObjectReference(type="group", id="eng"), relation="member")
    assert subject_set.object == ObjectReference(type="group", id="eng")
    assert subject_set.relation == "member"


@mark.unit
def test_subject_set_invalid_object_type_empty() -> None:
    """
    Test that an InvalidIdentifierError is raised when the object's type is invalid.
    """
    with raises(InvalidIdentifierError):
        SubjectSet(object=ObjectReference(type="", id="eng"), relation="member")


@mark.unit
def test_subject_set_invalid_relation_empty() -> None:
    """
    Test that an InvalidIdentifierError is raised when relation is invalid.
    """
    with raises(InvalidIdentifierError):
        SubjectSet(object=ObjectReference(type="group", id="eng"), relation="")


@mark.unit
def test_subject_set_equality() -> None:
    """
    Test that two SubjectSet instances with the same object and relation are equal.
    """
    assert SubjectSet(object=ObjectReference(type="group", id="eng"), relation="member") == SubjectSet(
        object=ObjectReference(type="group", id="eng"), relation="member"
    )


@mark.unit
def test_subject_set_inequality_different_object() -> None:
    """
    Test that two SubjectSet instances with a different object are not equal.
    """
    assert SubjectSet(object=ObjectReference(type="group", id="eng"), relation="member") != SubjectSet(
        object=ObjectReference(type="group", id="backend"), relation="member"
    )


@mark.unit
def test_subject_set_inequality_different_relation() -> None:
    """
    Test that two SubjectSet instances with a different relation are not equal.
    """
    assert SubjectSet(object=ObjectReference(type="group", id="eng"), relation="member") != SubjectSet(
        object=ObjectReference(type="group", id="eng"), relation="owner"
    )


@mark.unit
def test_subject_set_hash_consistency() -> None:
    """
    Test that equal SubjectSet instances have the same hash value.
    """
    assert hash(SubjectSet(object=ObjectReference(type="group", id="eng"), relation="member")) == hash(
        SubjectSet(object=ObjectReference(type="group", id="eng"), relation="member")
    )


@mark.unit
def test_subject_set_is_frozen() -> None:
    """
    Test that SubjectSet instances cannot be mutated after construction.
    """
    subject_set = SubjectSet(object=ObjectReference(type="group", id="eng"), relation="member")
    with raises(FrozenInstanceError):
        subject_set.object = ObjectReference(type="group", id="backend")  # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[invalid-assignment]

    with raises(FrozenInstanceError):
        subject_set.relation = "owner"  # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[invalid-assignment]
