"""
Test module for the reference module.
"""

from dataclasses import FrozenInstanceError

from pytest import raises

from policy_pattern.errors import InvalidIdentifierError
from policy_pattern.models import Reference


def test_reference_valid_construction() -> None:
    """
    Test that a valid Reference can be constructed without raising an error.
    """
    reference = Reference(name="owner")
    assert reference.name == "owner"


def test_reference_invalid_name_empty() -> None:
    """
    Test that an InvalidIdentifierError is raised when name is invalid.
    """
    with raises(InvalidIdentifierError):
        Reference(name="")


def test_reference_equality() -> None:
    """
    Test that two Reference instances with the same name are equal.
    """
    assert Reference(name="owner") == Reference(name="owner")


def test_reference_is_frozen() -> None:
    """
    Test that Reference instances cannot be mutated after construction.
    """
    reference = Reference(name="owner")
    with raises(FrozenInstanceError):
        reference.name = "editor"  # ty: ignore[invalid-assignment]


def test_reference_inequality_different_name() -> None:
    """
    Test that two Reference instances with different names are not equal.
    """
    assert Reference(name="owner") != Reference(name="editor")


def test_reference_hash_consistency() -> None:
    """
    Test that the hash of two Reference instances with the same name is equal.
    """
    reference1 = Reference(name="owner")
    reference2 = Reference(name="owner")
    assert hash(reference1) == hash(reference2)
