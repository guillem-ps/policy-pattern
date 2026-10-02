"""
Value Object representing a set of subjects in the authorization graph.
"""

from dataclasses import dataclass
from typing import ClassVar

from .identifier import Identifier
from .object_reference import ObjectReference


@dataclass(frozen=True, slots=True)
class SubjectSet:
    """
    Value Object representing a set of subjects.

    A subject set is a reference to *a relation on an object* — not a
    single entity like `DirectSubject`/`ObjectReference`, but the set of
    whoever holds that relation. `group:eng#member` refers to every
    current member of `group:eng`, resolved at evaluation time, not a
    fixed list stored here.

    This is the other half of `Subject` (`Subject = DirectSubject |
    SubjectSet`): `DirectSubject` names one entity;
    `SubjectSet` names a computation over the graph ("whoever satisfies
    this relation on this object right now"). It is exactly how nested
    groups work in Zanzibar — `group:eng#member@group:backend#member`
    makes every member of `group:backend` a member of `group:eng`,
    without ever copying a membership list.

    `relation` delegates to `Identifier` like every other identifier-shaped
    field in this model (`ObjectReference.type`/`.id`,
    `Relation.allowed_subject_types` entries) — no separate bounds/charset
    logic, no separate error class needed for it.

    Example:
        SubjectSet(object=ObjectReference(type="group", id="eng"), relation="member")

    `object` is validated by `ObjectReference` itself; `relation` is
    validated as an `Identifier` with `field="relation"`.

    Raises:
        InvalidIdentifierError: Propagated from `Identifier` if `relation` is invalid,
            or from `ObjectReference` if `type`/`id` is invalid.
    """

    object: ObjectReference
    relation: str

    _RELATION_IDENTIFIER_FIELD: ClassVar[str] = "relation"

    def __post_init__(self) -> None:
        """
        Validates the subject set after initialization by delegating to Identifier.
        """
        Identifier(value=self.relation, field=self._RELATION_IDENTIFIER_FIELD)
