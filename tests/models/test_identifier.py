"""
Test module for the Identifier class.
"""

from dataclasses import FrozenInstanceError

from pytest import mark, raises

from policy_pattern.errors import InvalidIdentifierError
from policy_pattern.models import Identifier


@mark.unit
def test_identifier_valid_construction() -> None:
    """
    Test that a valid Identifier can be constructed without raising an error. Happy value test.
    """
    identifier = Identifier(value="42", field="document")
    assert identifier.value == "42"
    assert identifier.field == "document"


@mark.unit
def test_identifier_invalid_value_length_less_than_min() -> None:
    """
    Test that an InvalidIdentifierError is raised when the identifier value length is less than the minimum.
    """
    with raises(InvalidIdentifierError) as exc_info:
        Identifier(value="", field="document")

    assert exc_info.value.message == (
        f"identifier value length must be between {Identifier._MIN_VALUE_LENGTH} and {Identifier._MAX_VALUE_LENGTH}"  # pyright: ignore[reportPrivateUsage]
    )


@mark.unit
def test_identifier_invalid_value_length_greater_than_max() -> None:
    """
    Test that an InvalidIdentifierError is raised when the identifier value length exceeds the maximum allowed length.
    """
    with raises(InvalidIdentifierError) as exc_info:
        Identifier(value="a" * 256, field="document")

    assert exc_info.value.message == (
        f"identifier value length must be between {Identifier._MIN_VALUE_LENGTH} and {Identifier._MAX_VALUE_LENGTH}"  # pyright: ignore[reportPrivateUsage]
    )


@mark.unit
def test_identifier_invalid_value_non_printable() -> None:
    """
    Test that an InvalidIdentifierError is raised when the identifier value contains non-printable characters.
    """
    invalid_value: str = "invalid\x00value"
    with raises(InvalidIdentifierError) as exc_info:
        Identifier(value=invalid_value, field="document")

    assert exc_info.value.message == f"identifier value {invalid_value!r} must contain printable characters only"


@mark.unit
def test_identifier_invalid_value_with_whitespace() -> None:
    """
    Test that an InvalidIdentifierError is raised when the identifier value contains leading or trailing whitespace.
    """
    with raises(InvalidIdentifierError) as exc_info:
        Identifier(value=" 42 ", field="document")

    assert exc_info.value.message == "identifier value ' 42 ' cannot contain leading or trailing whitespace"


@mark.unit
def test_identifier_invalid_field_empty() -> None:
    """
    Test that an InvalidIdentifierError is raised when the identifier field is empty.
    """
    with raises(InvalidIdentifierError) as exc_info:
        Identifier(value="42", field="")

    assert exc_info.value.message == "identifier field cannot be empty"


@mark.unit
def test_identifier_equality() -> None:
    """Test that two Identifier instances with the same value and field are equal."""
    assert Identifier(value="42", field="document") == Identifier(value="42", field="document")


@mark.unit
def test_identifier_inequality_different_value() -> None:
    """Test that two Identifier instances with different values are not equal."""
    assert Identifier(value="42", field="document") != Identifier(value="43", field="document")


@mark.unit
def test_identifier_case_sensitive() -> None:
    """Test that Identifier equality is case-sensitive."""
    assert Identifier(value="User", field="document") != Identifier(value="user", field="document")


@mark.unit
def test_identifier_no_unicode_normalization() -> None:
    """Test that Identifier does not normalize Unicode — precomposed and decomposed forms are not equal."""
    precomposed = Identifier(value="\u00e9", field="document")  # "é"
    decomposed = Identifier(value="e\u0301", field="document")  # "e" + combining acute accent
    assert precomposed != decomposed


@mark.unit
def test_identifier_hash_consistency() -> None:
    """Test that equal Identifier instances have the same hash."""
    assert hash(Identifier(value="42", field="document")) == hash(Identifier(value="42", field="document"))


@mark.unit
def test_identifier_is_frozen() -> None:
    """Test that Identifier instances cannot be mutated after construction."""
    identifier = Identifier(value="42", field="document")
    with raises(FrozenInstanceError):
        identifier.value = "43"  # ty: ignore[invalid-assignment]

    with raises(FrozenInstanceError):
        identifier.field = "other"  # ty: ignore[invalid-assignment]


@mark.unit
def test_identifier_allows_colon_hash_at_characters() -> None:
    """Test that ':', '#', and '@' are valid identifier value characters, not restricted."""
    assert Identifier(value="user:tests", field="subject").value == "user:tests"
    assert Identifier(value="group:eng#member", field="subject").value == "group:eng#member"
    assert Identifier(value="tests@example.com", field="subject").value == "tests@example.com"


@mark.unit
def test_identifier_valid_value_length_at_min_boundary() -> None:
    """Test that a value of exactly the minimum allowed length is valid."""
    identifier = Identifier(value="a" * Identifier._MIN_VALUE_LENGTH, field="document")  # pyright: ignore[reportPrivateUsage]
    assert len(identifier.value) == Identifier._MIN_VALUE_LENGTH  # pyright: ignore[reportPrivateUsage]


@mark.unit
def test_identifier_valid_value_length_at_max_boundary() -> None:
    """Test that a value of exactly the maximum allowed length is valid."""
    identifier = Identifier(value="a" * Identifier._MAX_VALUE_LENGTH, field="document")  # pyright: ignore[reportPrivateUsage]
    assert len(identifier.value) == Identifier._MAX_VALUE_LENGTH  # pyright: ignore[reportPrivateUsage]
