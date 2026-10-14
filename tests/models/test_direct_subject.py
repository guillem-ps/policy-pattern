"""
Test module for the DirectSubject class.
"""

from dataclasses import FrozenInstanceError

from pytest import mark, raises

from policy_pattern.errors import InvalidIdentifierError
from policy_pattern.models import DirectSubject, ObjectReference


@mark.unit
def test_direct_subject_valid_construction() -> None:
    """
    Test that a valid DirectSubject can be constructed without raising an error. Happy value test.
    """
    direct_subject = DirectSubject(object=ObjectReference(type="user", id="john"))
    assert direct_subject.object == ObjectReference(type="user", id="john")


@mark.unit
def test_direct_subject_invalid_type_empty() -> None:
    """
    Test that an InvalidIdentifierError is raised when the DirectSubject type is invalid.
    """
    with raises(InvalidIdentifierError):
        DirectSubject(object=ObjectReference(type="", id="john"))


@mark.unit
def test_direct_subject_invalid_id_empty() -> None:
    """
    Test that an InvalidIdentifierError is raised when the DirectSubject id is invalid.
    """
    with raises(InvalidIdentifierError):
        DirectSubject(object=ObjectReference(type="user", id=""))


@mark.unit
def test_direct_subject_equality() -> None:
    """
    Test that two DirectSubject instances with the same type and id are equal.
    """
    assert DirectSubject(object=ObjectReference(type="user", id="john")) == DirectSubject(
        object=ObjectReference(type="user", id="john")
    )


@mark.unit
def test_direct_subject_is_frozen() -> None:
    """
    Test that DirectSubject instances cannot be mutated after construction.
    """
    direct_subject = DirectSubject(object=ObjectReference(type="user", id="john"))
    with raises(FrozenInstanceError):
        direct_subject.object = ObjectReference(type="user", id="doe")  # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[invalid-assignment]


@mark.unit
def test_direct_subject_inequality_different_type() -> None:
    """
    Test that two DirectSubject instances with different type are not equal.
    """
    assert DirectSubject(object=ObjectReference(type="user", id="john")) != DirectSubject(
        object=ObjectReference(type="admin", id="john")
    )


@mark.unit
def test_direct_subject_inequality_different_id() -> None:
    """
    Test that two DirectSubject instances with different id are not equal.
    """
    assert DirectSubject(object=ObjectReference(type="user", id="john")) != DirectSubject(
        object=ObjectReference(type="user", id="doe")
    )


@mark.unit
def test_direct_subject_hash_consistency() -> None:
    """
    Test that equal DirectSubject instances have the same hash value.
    """
    assert hash(DirectSubject(object=ObjectReference(type="user", id="john"))) == hash(
        DirectSubject(object=ObjectReference(type="user", id="john"))
    )
