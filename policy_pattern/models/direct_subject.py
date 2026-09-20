"""
Value Object representing a reference to a concrete subject in the authorization graph.
Example:
    user:john.
"""

from dataclasses import dataclass

from .object_reference import ObjectReference


@dataclass(frozen=True, slots=True)
class DirectSubject:
    """
    Value Object representing a concrete subject in the authorization graph.

    A direct subject wraps the object it refers to - e.g. `user:john` is
    `DirectSubject(object=ObjectReference(type="user", id="john"))`.
    """

    object: ObjectReference
