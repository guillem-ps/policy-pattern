"""
Test module for the tuple to userset model.
"""

from dataclasses import FrozenInstanceError

from pytest import raises

from policy_pattern.errors import InvalidIdentifierError
from policy_pattern.models.tuple_to_userset import TupleToUserset


def test_tuple_to_userset_valid_construction() -> None:
    """
    Test that a valid TupleToUserset can be constructed without raising an error.
    """
    tuple_to_userset = TupleToUserset(
        tupleset="parent",
        computed="viewer",
    )
    assert tuple_to_userset.tupleset == "parent"
    assert tuple_to_userset.computed == "viewer"


def test_tuple_to_userset_equality() -> None:
    """
    Test that two TupleToUserset instances with the same tupleset and computed are equal.
    """
    assert TupleToUserset(tupleset="parent", computed="viewer") == TupleToUserset(tupleset="parent", computed="viewer")


def test_tuple_to_userset_inequality_different_tupleset() -> None:
    """
    Test that two TupleToUserset instances with a different tupleset are not equal.
    """
    assert TupleToUserset(tupleset="parent", computed="viewer") != TupleToUserset(tupleset="child", computed="viewer")


def test_tuple_to_userset_inequality_different_computed() -> None:
    """
    Test that two TupleToUserset instances with a different computed are not equal.
    """
    assert TupleToUserset(tupleset="parent", computed="viewer") != TupleToUserset(tupleset="parent", computed="editor")


def test_tuple_to_userset_is_frozen() -> None:
    """
    Test that TupleToUserset instances cannot be mutated after construction.
    """
    tuple_to_userset = TupleToUserset(tupleset="parent", computed="viewer")
    with raises(FrozenInstanceError):
        tuple_to_userset.tupleset = "child"  # ty: ignore[invalid-assignment]

    with raises(FrozenInstanceError):
        tuple_to_userset.computed = "editor"  # ty: ignore[invalid-assignment]


def test_tuple_to_userset_invalid_tupleset_empty() -> None:
    """
    Test that an InvalidIdentifierError is raised when the tupleset is invalid.
    """
    with raises(InvalidIdentifierError):
        TupleToUserset(tupleset="", computed="viewer")


def test_tuple_to_userset_invalid_computed_empty() -> None:
    """
    Test that an InvalidIdentifierError is raised when the computed is invalid.
    """
    with raises(InvalidIdentifierError):
        TupleToUserset(tupleset="parent", computed="")
