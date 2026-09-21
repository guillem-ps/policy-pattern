"""
Value Object representing a declaration mutable at authoring time, but immutable at evaluation time.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import ClassVar

from .identifier import Identifier
from .operators import PermissionExpression
from .relation import Relation


@dataclass(frozen=True, slots=True)
class Type:
    """
    Value Object representing a type declaration in the authorization graph.

    A `Type` declares a kind of object, along with the relations and
    permissions it supports.

    Example:
        Type(name="document")

    Raises:
        InvalidIdentifierError: Propagated from `Identifier` if `name` is invalid.
    """

    name: str
    relations: Mapping[str, Relation]
    permissions: Mapping[str, PermissionExpression]

    _TYPE_NAME_FIELD: ClassVar[str] = "type"

    def __post_init__(self) -> None:
        """
        Validate `name`, and make `relations`/`permissions` a read-only view.

        `frozen=True` only blocks reassigning `relations`/`permissions`
        themselves — a plain `dict` field would still be mutable in place
        (`type_.relations["x"] = y`). Wrapping a copy in `MappingProxyType`
        closes that gap: neither the returned view nor the caller's
        original dict (once copied) can affect this instance afterward.
        """
        Identifier(value=self.name, field=self._TYPE_NAME_FIELD)
        object.__setattr__(self, "relations", MappingProxyType(dict(self.relations)))
        object.__setattr__(self, "permissions", MappingProxyType(dict(self.permissions)))
