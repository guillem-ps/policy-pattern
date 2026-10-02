"""
Value Object representing a reference to a concrete object in the authorization graph.
"""

from dataclasses import dataclass
from typing import ClassVar

from .identifier import Identifier


@dataclass(frozen=True, slots=True)
class ObjectReference:
    """
    Value Object representing a concrete object.

    An object reference identifies a specific entity by its type and id —
    e.g. "document:42" is the type "document" with id "42". Both `type`
    and `id` are validated as identifiers (see `Identifier`): non-empty,
    bounded length, printable characters only.

    Example:
        ObjectReference(type="document", id="42")

    Both components are validated as `Identifier` values with fields
    `"type"` and `"id"`, respectively.
    """

    type: str
    id: str

    _FIELD_TYPE_VALUE: ClassVar[str] = "type"
    _FIELD_ID_VALUE: ClassVar[str] = "id"

    def __post_init__(self) -> None:
        """
        Validates the object reference after initialization by delegating to Identifier.

        Raises:
            InvalidIdentifierError: If `type` or `id` is invalid.
        """
        Identifier(value=self.type, field=self._FIELD_TYPE_VALUE)
        Identifier(value=self.id, field=self._FIELD_ID_VALUE)
