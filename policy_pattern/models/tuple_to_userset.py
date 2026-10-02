"""
Value Object representing a computed permission expression that traverses to a
related object via a relation and evaluates a computed permission there.
"""

from dataclasses import dataclass
from typing import ClassVar

from .identifier import Identifier
from .operators import PermissionExpression


@dataclass(frozen=True, slots=True)
class TupleToUserset(PermissionExpression):
    """
    Traverses to a related object via `tupleset`, then evaluates `computed` there.

    This is the one node that is not a set operation on *this* object — it
    jumps to a *different* object first. `document:42#parent@folder:eng`
    plus `TupleToUserset(tupleset="parent", computed="viewer")` reads as
    "find the object(s) related to this one via `parent`, then check
    `viewer` on *that* object instead." It is how folder hierarchies grant
    access to every document underneath without copying a permission onto
    each child individually, and how nested groups
    (`group:eng#member@group:backend#member`) work without flattening
    membership into a stored list.

    `tupleset` must resolve to a `Relation`, never a `Permission` —
    traversal needs an actual stored edge to follow (`document:42#parent`
    has to exist as data); there is nothing to traverse if `parent` were
    itself a computed rule. `computed` has no such restriction: it is
    evaluated on the object found via `tupleset`, and can be either a
    `Relation` or another `Permission` there, resolved the same way
    `Reference` resolves its own `name`.

    Example:
        TupleToUserset(tupleset="parent", computed="viewer")
    """

    tupleset: str
    computed: str

    _FIELD_TUPLESET_VALUE: ClassVar[str] = "tupleset"
    _FIELD_COMPUTED_VALUE: ClassVar[str] = "computed"

    def __post_init__(self) -> None:
        """
        Validates `tupleset` and `computed` by delegating to `Identifier`.
        """
        Identifier(value=self.tupleset, field=self._FIELD_TUPLESET_VALUE)
        Identifier(value=self.computed, field=self._FIELD_COMPUTED_VALUE)
