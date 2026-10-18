"""
Test module for the ObjectReference class.
"""

from unittest.mock import patch

from pytest import mark, raises

from policy_pattern.errors import InvalidIdentifierError
from policy_pattern.models import ObjectReference


@mark.unit
def test_object_reference_valid_construction() -> None:
    """Test that a valid ObjectReference can be constructed without raising an error."""
    reference = ObjectReference(type="document", id="42")
    assert reference.type == "document"
    assert reference.id == "42"


@mark.unit
def test_object_reference_invalid_type_empty() -> None:
    """Test that an InvalidIdentifierError is raised when type is invalid."""
    with raises(InvalidIdentifierError):
        ObjectReference(type="", id="42")


@mark.unit
def test_object_reference_invalid_id_empty() -> None:
    """Test that an InvalidIdentifierError is raised when id is invalid."""
    with raises(InvalidIdentifierError):
        ObjectReference(type="document", id="")


@mark.unit
def test_object_reference_equality() -> None:
    """Test that two ObjectReference instances with the same type and id are equal."""
    assert ObjectReference(type="document", id="42") == ObjectReference(type="document", id="42")


@mark.unit
def test_object_reference_is_frozen() -> None:
    """Test that ObjectReference instances cannot be mutated after construction."""
    from dataclasses import FrozenInstanceError

    reference = ObjectReference(type="document", id="42")
    with raises(FrozenInstanceError):
        reference.type = "other"  # ty: ignore[invalid-assignment]

    with raises(FrozenInstanceError):
        reference.id = "43"  # ty: ignore[invalid-assignment]


@mark.unit
def test_object_reference_creates_identifiers() -> None:
    """Test that constructing an ObjectReference actually creates Identifier instances for type and id."""
    with patch("policy_pattern.models.object_reference.Identifier") as mock_identifier:
        ObjectReference(type="document", id="42")

    assert mock_identifier.call_count == 2
    mock_identifier.assert_any_call(value="document", field="type")
    mock_identifier.assert_any_call(value="42", field="id")


@mark.unit
def test_object_reference_inequality_different_type() -> None:
    """Test that two ObjectReference instances with different type are not equal."""
    assert ObjectReference(type="document", id="42") != ObjectReference(type="folder", id="42")


@mark.unit
def test_object_reference_inequality_different_id() -> None:
    """Test that two ObjectReference instances with different id are not equal."""
    assert ObjectReference(type="document", id="42") != ObjectReference(type="document", id="43")


@mark.unit
def test_object_reference_hash_consistency() -> None:
    """Test that equal ObjectReference instances have the same hash."""
    assert hash(ObjectReference(type="document", id="42")) == hash(ObjectReference(type="document", id="42"))
