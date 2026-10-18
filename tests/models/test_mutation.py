"""
Test module for the Mutation class.
"""

from dataclasses import FrozenInstanceError

from pytest import mark, raises

from policy_pattern.errors import InvalidMutationError
from policy_pattern.models import DirectSubject, Mutation, ObjectReference, Tuple


def _tuple(id_: str = "42") -> Tuple:
    """
    Helper function to create a Tuple with default values.
    """
    return Tuple(
        subject=DirectSubject(object=ObjectReference(type="user", id="john")),
        relation="owner",
        object=ObjectReference(type="document", id=id_),
    )


@mark.unit
def test_mutation_valid_construction() -> None:
    """
    Test that a valid Mutation can be constructed without raising an error.
    """
    mutation = Mutation(additions=frozenset({_tuple("42")}), deletions=frozenset({_tuple("43")}))
    assert mutation.additions == frozenset({_tuple("42")})
    assert mutation.deletions == frozenset({_tuple("43")})


@mark.unit
def test_mutation_empty_is_valid() -> None:
    """
    Test that an empty Mutation (no additions, no deletions) is valid.
    """
    mutation = Mutation(additions=frozenset(), deletions=frozenset())
    assert mutation.additions == frozenset()
    assert mutation.deletions == frozenset()


@mark.unit
def test_mutation_invalid_not_disjoint() -> None:
    """
    Test that an InvalidMutationError is raised when additions and deletions overlap.
    """
    with raises(InvalidMutationError):
        Mutation(additions=frozenset({_tuple("42")}), deletions=frozenset({_tuple("42")}))


@mark.unit
def test_mutation_equality() -> None:
    """
    Test that two Mutation instances with the same additions and deletions are equal.
    """
    assert Mutation(additions=frozenset({_tuple("42")}), deletions=frozenset()) == Mutation(
        additions=frozenset({_tuple("42")}), deletions=frozenset()
    )


@mark.unit
def test_mutation_inequality_different_additions() -> None:
    """
    Test that two Mutation instances with different additions are not equal.
    """
    assert Mutation(additions=frozenset({_tuple("42")}), deletions=frozenset()) != Mutation(
        additions=frozenset({_tuple("43")}), deletions=frozenset()
    )


@mark.unit
def test_mutation_inequality_different_deletions() -> None:
    """
    Test that two Mutation instances with different deletions are not equal.
    """
    assert Mutation(additions=frozenset(), deletions=frozenset({_tuple("42")})) != Mutation(
        additions=frozenset(), deletions=frozenset({_tuple("43")})
    )


@mark.unit
def test_mutation_hash_consistency() -> None:
    """
    Test that equal Mutation instances have the same hash value.
    """
    assert hash(Mutation(additions=frozenset({_tuple("42")}), deletions=frozenset())) == hash(
        Mutation(additions=frozenset({_tuple("42")}), deletions=frozenset())
    )


@mark.unit
def test_mutation_is_frozen() -> None:
    """
    Test that Mutation instances cannot be mutated after construction.
    """
    mutation = Mutation(additions=frozenset({_tuple("42")}), deletions=frozenset())

    with raises(FrozenInstanceError):
        mutation.additions = frozenset()  # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[invalid-assignment]

    with raises(FrozenInstanceError):
        mutation.deletions = frozenset({_tuple("43")})  # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[invalid-assignment]
