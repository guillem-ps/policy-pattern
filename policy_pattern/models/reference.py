"""
Value object representing a reference to a relation or permission on the same type.
"""

from dataclasses import dataclass

from .identifier import Identifier
from .operators import PermissionExpression


@dataclass(frozen=True, slots=True)
class Reference(PermissionExpression):
    """
    Names a relation or permission on the same type — the leaf case.

    `Reference` is deliberately the *only* leaf node type, unifying what
    an earlier draft of this design split into two (`This`, for stored
    relations, and `ComputedUserset`, for other permissions). At authoring
    time there is no way to tell which one `name` refers to without
    looking at the rest of the type's declarations — so the distinction is
    resolved once, by the evaluator, at evaluation time: if `name` is a
    declared `Relation`, look it up in the `TupleStore`; if it is another
    `Permission`, recurse into its own expression tree. Neither case is
    knowable — or needs to be knowable — from `Reference` alone.

    Example:
        Reference(name="owner")
    """

    name: str

    def __post_init__(self) -> None:
        """
        Validates `name` by delegating to `Identifier`.
        """
        Identifier(value=self.name, field="name")
