"""
Value Object representing an atomic write to the authorization store.
"""

from dataclasses import dataclass

from policy_pattern.errors import InvalidMutationError

from .tuple import Tuple


@dataclass(frozen=True, slots=True)
class Mutation:
    """
    Value Object representing one atomic write: a set of additions and a
    set of deletions applied together, or not at all.

    S' = (S - deletions) | additions

    `additions`/`deletions` must be disjoint — a tuple present in both has
    no defined meaning (`semantics.md`). An empty mutation
    (`additions=frozenset(), deletions=frozenset()`) is valid: a no-op,
    not a special case to reject.

    Unlike every other Value Object so far, `Mutation` has no
    identifier-shaped field of its own to delegate to `Identifier` — its
    only rule is structural (the two sets don't overlap), not a bounds/
    charset check.

    Example:
        Mutation(additions=frozenset({tuple_a}), deletions=frozenset({tuple_b}))

    Raises:
        InvalidMutationError: If `additions` and `deletions` are not disjoint.

    Attributes:
        additions (frozenset[Tuple]): The set of tuples to add.
        deletions (frozenset[Tuple]): The set of tuples to delete.
    """

    additions: frozenset[Tuple]
    deletions: frozenset[Tuple]

    def __post_init__(self) -> None:
        """
        Validates that additions and deletions are disjoint.

        An empty mutation (no additions, no deletions) is valid — a no-op,
        not an error.
        """
        if self.additions & self.deletions:
            raise InvalidMutationError(message="additions and deletions must be disjoint")
