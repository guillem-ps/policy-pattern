"""This module contains a factory function to create representative tuples for tests."""

from policy_pattern.models import DirectSubject, ObjectReference, Tuple


def make_tuple(id_: str) -> Tuple:
    """Create a representative tuple for tests."""
    return Tuple(
        subject=DirectSubject(object=ObjectReference(type="user", id=id_)),
        relation="owner",
        object=ObjectReference(type="document", id="42"),
    )
