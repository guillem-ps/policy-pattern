"""
Value Object representing a reference to a concrete subject in the authorization graph.
"""

from dataclasses import dataclass

from .object_reference import ObjectReference


@dataclass(frozen=True, slots=True)
class DirectSubject:
    """
    Value Object representing a concrete subject in the authorization graph.

    A direct subject is theoretically the same kind of entity as an
    `ObjectReference` — Zanzibar's own data model defines a "user" (a
    direct subject) as exactly the same `<namespace>:<id>` shape as an
    object. The only difference is the *role* it plays inside a `Tuple`
    (subject side, not object side), never what kind of thing it is —
    the same entity can be the object of one tuple
    (`user:john#manager@user:jane`, where `user:john` is the object) and
    the direct subject of another (`document:42#owner@user:john`).

    Because of that, `DirectSubject` wraps an `ObjectReference` instead of
    redeclaring `type`/`id` and their validation: any invalid `type`/`id`
    already fails inside the `ObjectReference(...)` call, before
    `DirectSubject` is ever constructed — there is nothing left for this
    class to validate on its own.

    This is one half of `Subject` (`Subject = DirectSubject | SubjectSet`,
    not yet implemented) — the other half, `SubjectSet`, is a genuinely
    different concept: not a single entity, but a reference to *a relation
    on an object* (`group:eng#member`), i.e. a set of subjects rather than
    one.

    Example:
        DirectSubject(object=ObjectReference(type="user", id="john"))
    Equals:
        ObjectReference(type="user", id="john") -> Identifier(
            value="user", field="type"
        ) and Identifier(value="john", field="id") -> user:john

    Raises:
        InvalidIdentifierError: Propagated from `ObjectReference` if `type` or `id` is invalid.
    """

    object: ObjectReference
