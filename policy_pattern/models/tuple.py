"""
Value Object representing a stored relationship fact in the authorization graph.
"""

from dataclasses import dataclass

from .identifier import Identifier
from .object_reference import ObjectReference
from .subject import Subject


@dataclass(frozen=True, slots=True)
class Tuple:
    """
    Value Object representing one stored fact: `object#relation@subject`.

    e.g. `document:42#owner@user:john` is
    `Tuple(subject=DirectSubject(object=ObjectReference(type="user", id="john")),
    relation="owner", object=ObjectReference(type="document", id="42"))`.

    `relation` only names a relation here — it is validated as an
    `Identifier` (non-empty, bounded, printable), but *not* checked against
    an actual `Relation`/`Permission` declaration. `Tuple` has no schema
    context to check that against; confirming `relation` actually names a
    storable `Relation` (never a `Permission`) is `compile()`'s job on the
    `Model`, not this class's.

    `subject`/`object` are validated by `Subject`'s variants
    (`DirectSubject`/`SubjectSet`) and `ObjectReference` themselves —
    `Tuple` only validates the one field it owns directly.

    Example:
        Tuple(
            subject=DirectSubject(object=ObjectReference(type="user", id="john")),
            relation="owner",
            object=ObjectReference(type="document", id="42"),
        )

    Raises:
        InvalidIdentifierError: If `relation` is invalid, or propagated from
            `subject`/`object` construction.
    """

    subject: Subject
    relation: str
    object: ObjectReference

    def __post_init__(self) -> None:
        """
        Validates the tuple after initialization by delegating relation to Identifier.
        """
        Identifier(value=self.relation, field="relation")
