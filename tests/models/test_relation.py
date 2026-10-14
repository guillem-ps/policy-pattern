"""
Test module for the Relation class.
"""

from dataclasses import FrozenInstanceError

from pytest import mark, raises

from policy_pattern.errors import InvalidIdentifierError, InvalidRelationError
from policy_pattern.models import Relation


@mark.unit
def test_relation_valid_construction() -> None:
    """
    Test that a valid Relation can be constructed without raising an error.
    """
    relation = Relation(allowed_subject_types=("user", "organization#member"))
    assert relation.allowed_subject_types == ("user", "organization#member")


@mark.unit
def test_relation_invalid_empty_allowed_subject_types() -> None:
    """
    Test that an InvalidRelationError is raised when allowed_subject_types is empty.
    """
    with raises(InvalidRelationError) as exc_info:
        Relation(allowed_subject_types=())

    assert exc_info.value.message == "relation must declare at least one allowed subject type"


@mark.unit
def test_relation_allowed_subject_types_invalid_entry() -> None:
    """
    Test that an InvalidIdentifierError is raised when allowed_subject_types contains an invalid entry.
    """
    invalid_value: str = "invalid\x00value"
    with raises(InvalidIdentifierError) as exc_info:
        Relation(allowed_subject_types=("user", invalid_value))

    assert exc_info.value.message == f"identifier value {invalid_value!r} must contain printable characters only"


@mark.unit
def test_relation_equality() -> None:
    """
    Test that two Relation instances with the same allowed_subject_types are equal.
    """
    relation1 = Relation(allowed_subject_types=("user", "organization#member"))
    relation2 = Relation(allowed_subject_types=("user", "organization#member"))
    assert relation1 == relation2


@mark.unit
def test_relation_is_frozen() -> None:
    """
    Test that Relation instances cannot be mutated after construction.
    """
    relation = Relation(allowed_subject_types=("user", "organization#member"))
    with raises(FrozenInstanceError):
        relation.allowed_subject_types = ("other",)  # ty: ignore[invalid-assignment]


@mark.unit
def test_relation_inequality_different_allowed_subject_types() -> None:
    """Test that two Relation instances with different allowed_subject_types are not equal."""
    assert Relation(allowed_subject_types=("user",)) != Relation(allowed_subject_types=("group",))


@mark.unit
def test_relation_hash_consistency() -> None:
    """Test that equal Relation instances have the same hash."""
    relation1 = Relation(allowed_subject_types=("user", "organization#member"))
    relation2 = Relation(allowed_subject_types=("user", "organization#member"))
    assert hash(relation1) == hash(relation2)
