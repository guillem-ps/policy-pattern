"""
Value Object representing a declaration mutable at authoring time, but immutable at evaluation time.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import ClassVar

from policy_pattern.errors import InvalidIdentifierError

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
        Type(name="document", relations={}, permissions={})

    Raises:
        InvalidIdentifierError: Propagated from `Identifier` if `name`, a
            relation name, or a permission name is invalid, or if `name`
            contains '#' (reserved for userset notation).
    """

    name: str
    relations: Mapping[str, Relation]
    permissions: Mapping[str, PermissionExpression]

    _TYPE_NAME_FIELD: ClassVar[str] = "type"
    _RELATION_NAME_FIELD: ClassVar[str] = "relation"
    _PERMISSION_NAME_FIELD: ClassVar[str] = "permission"

    def __post_init__(self) -> None:
        """
        Validate `name` and every relation/permission name, then make the mappings read-only views.

        `relations`/`permissions` keys are the actual schema identifiers —
        `Reference`/`tupleset` names resolve against them — so they need the
        same `Identifier` validation as `name` itself, not just the values.

        `frozen=True` only blocks reassigning `relations`/`permissions`
        themselves — a plain `dict` field would still be mutable in place
        (`type_.relations["x"] = y`). Wrapping a copy in `MappingProxyType`
        closes that gap: neither the returned view nor the caller's
        original dict (once copied) can affect this instance afterward.
        """
        Identifier(value=self.name, field=self._TYPE_NAME_FIELD)
        if "#" in self.name:
            # Reserved for userset notation ("type#relation") inside
            # Relation.allowed_subject_types — _schema_validation.py tells a
            # plain type-name entry apart from a userset one by checking for
            # "#" in the string. If a real Type name could contain "#" too,
            # that check couldn't tell them apart.
            raise InvalidIdentifierError(
                message=f"type name {self.name!r} cannot contain '#' — reserved for userset notation",
                related=f"field={self._TYPE_NAME_FIELD!r}",
            )
        for relation_name in self.relations:
            Identifier(value=relation_name, field=self._RELATION_NAME_FIELD)
        for permission_name in self.permissions:
            Identifier(value=permission_name, field=self._PERMISSION_NAME_FIELD)
        object.__setattr__(self, "relations", MappingProxyType(dict(self.relations)))
        object.__setattr__(self, "permissions", MappingProxyType(dict(self.permissions)))
