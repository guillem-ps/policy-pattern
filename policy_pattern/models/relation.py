"""
Value Object representing a storable relation on an object type.
"""

from dataclasses import dataclass

from policy_pattern.errors import InvalidRelationError

from .identifier import Identifier


@dataclass(frozen=True, slots=True)
class Relation:
    """
    Value Object representing a storable relation.

    A relation is a storable edge — a fact that can exist directly in the
    TupleStore, e.g. `document:42#owner@user:alice`. It carries no rewrite
    algebra (that's `PermissionExpression`'s job); it only restricts which
    subject types are allowed to hold it. Each entry is a type name
    ("user") or a userset restriction ("organization#member") — the same
    textual shape as a SubjectSet.

    Example:
        Relation(allowed_subject_types=("user", "organization#member"))

    Each allowed subject type is validated as an `Identifier` with
    `field="allowed_subject_types"`.
    """

    allowed_subject_types: tuple[str, ...]

    def __post_init__(self) -> None:
        """
        Validates the relation after initialization.

        Raises:
            InvalidRelationError: If `allowed_subject_types` is empty or contains an invalid entry.
        """
        if not self.allowed_subject_types:
            raise InvalidRelationError(message="relation must declare at least one allowed subject type")

        for subject_type in self.allowed_subject_types:
            Identifier(value=subject_type, field="allowed_subject_types")
