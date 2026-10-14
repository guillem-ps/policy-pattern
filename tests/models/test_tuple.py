"""
Test module for the Tuple class.
"""

from dataclasses import FrozenInstanceError

from pytest import mark, raises

from policy_pattern.errors import InvalidIdentifierError
from policy_pattern.models import DirectSubject, ObjectReference, Tuple


def _direct_subject(id_: str = "john") -> DirectSubject:
    """
    Helper function to create a DirectSubject with a default id.
    """
    return DirectSubject(object=ObjectReference(type="user", id=id_))


def _object(id_: str = "42") -> ObjectReference:
    """
    Helper function to create an ObjectReference with a default id.
    """
    return ObjectReference(type="document", id=id_)


@mark.unit
def test_tuple_valid_construction() -> None:
    """
    Test that a valid Tuple can be constructed without raising an error.
    """
    tuple_ = Tuple(subject=_direct_subject(), relation="owner", object=_object())
    assert tuple_.subject == _direct_subject()
    assert tuple_.relation == "owner"
    assert tuple_.object == _object()


@mark.unit
def test_tuple_invalid_relation_empty() -> None:
    """
    Test that an InvalidIdentifierError is raised when relation is invalid.
    """
    with raises(InvalidIdentifierError):
        Tuple(subject=_direct_subject(), relation="", object=_object())


@mark.unit
def test_tuple_invalid_object_type_empty() -> None:
    """
    Test that an InvalidIdentifierError is raised when the object's type is invalid.
    """
    with raises(InvalidIdentifierError):
        Tuple(subject=_direct_subject(), relation="owner", object=ObjectReference(type="", id="42"))


@mark.unit
def test_tuple_equality() -> None:
    """
    Test that two Tuple instances with the same subject, relation and object are equal.
    """
    assert Tuple(subject=_direct_subject(), relation="owner", object=_object()) == Tuple(
        subject=_direct_subject(), relation="owner", object=_object()
    )


@mark.unit
def test_tuple_inequality_different_subject() -> None:
    """
    Test that two Tuple instances with a different subject are not equal.
    """
    assert Tuple(subject=_direct_subject(), relation="owner", object=_object()) != Tuple(
        subject=_direct_subject(id_="jane"), relation="owner", object=_object()
    )


@mark.unit
def test_tuple_inequality_different_relation() -> None:
    """
    Test that two Tuple instances with a different relation are not equal.
    """
    assert Tuple(subject=_direct_subject(), relation="owner", object=_object()) != Tuple(
        subject=_direct_subject(), relation="viewer", object=_object()
    )


@mark.unit
def test_tuple_inequality_different_object() -> None:
    """
    Test that two Tuple instances with a different object are not equal.
    """
    assert Tuple(subject=_direct_subject(), relation="owner", object=_object()) != Tuple(
        subject=_direct_subject(), relation="owner", object=_object(id_="43")
    )


@mark.unit
def test_tuple_hash_consistency() -> None:
    """
    Test that equal Tuple instances have the same hash value.
    """
    assert hash(Tuple(subject=_direct_subject(), relation="owner", object=_object())) == hash(
        Tuple(subject=_direct_subject(), relation="owner", object=_object())
    )


@mark.unit
def test_tuple_is_frozen() -> None:
    """
    Test that Tuple instances cannot be mutated after construction.
    """
    tuple_ = Tuple(subject=_direct_subject(), relation="owner", object=_object())

    with raises(FrozenInstanceError):
        tuple_.subject = _direct_subject(id_="jane")  # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[invalid-assignment]

    with raises(FrozenInstanceError):
        tuple_.relation = "viewer"  # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[invalid-assignment]

    with raises(FrozenInstanceError):
        tuple_.object = _object(id_="43")  # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[invalid-assignment]
