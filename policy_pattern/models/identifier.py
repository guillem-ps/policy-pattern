"""
Value Object representing an entity identifier.
-Must be immutable, hashable, and comparable.
-An identifier contains the value that identifies an entity and
-the field/type associated with that identifier.
-Example:
-Identifier(value="42", field="document")
-Validation rules:
- document:42.
"""

from dataclasses import dataclass
from typing import ClassVar

from ..errors import InvalidIdentifierError


@dataclass(frozen=True, slots=True)
class Identifier:
    """
    Value Object representing an entity identifier.

    An identifier contains the value that identifies an entity and
    the field/type associated with that identifier.

    Example:
        Identifier(value="42", field="document")
    """

    value: str
    field: str

    _MIN_VALUE_LENGTH: ClassVar[int] = 1
    _MAX_VALUE_LENGTH: ClassVar[int] = 255

    def __post_init__(self) -> None:
        """
        Validates the identifier after initialization.

        Raises:
            InvalidIdentifierError: If the identifier value or field is invalid.
        """
        if not self._MIN_VALUE_LENGTH <= len(self.value) <= self._MAX_VALUE_LENGTH:
            raise InvalidIdentifierError(
                message=f"identifier value length must be between {self._MIN_VALUE_LENGTH!r} and {self._MAX_VALUE_LENGTH!r}",  # noqa: E501
                related=f"field={self.field!r}",
            )

        if not self.value.isprintable():
            raise InvalidIdentifierError(
                message=f"identifier value {self.value!r} must contain printable characters only",
                related=f"field={self.field!r}",
            )

        if self.value != self.value.strip():
            raise InvalidIdentifierError(
                message=f"identifier value {self.value!r} cannot contain leading or trailing whitespace",
                related=f"field={self.field!r}",
            )

        if not self.field:
            raise InvalidIdentifierError(message="identifier field cannot be empty")
