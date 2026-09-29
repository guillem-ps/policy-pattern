"""
Test module for the Type class.
"""

from dataclasses import FrozenInstanceError
from types import MappingProxyType

from pytest import raises

from policy_pattern.errors import InvalidIdentifierError
from policy_pattern.models import Reference, Relation, Type


def test_type_valid_construction() -> None:
    """
    Test that a valid Type can be constructed without raising an error.
    """
    type_ = Type(name="document", relations={}, permissions={})
    assert type_.name == "document"
    assert type_.relations == {}
    assert type_.permissions == {}


def test_type_invalid_name() -> None:
    """
    Test that an InvalidIdentifierError is raised when name is invalid.
    """
    with raises(InvalidIdentifierError):
        Type(name="", relations={}, permissions={})


def test_type_name_cannot_contain_hash() -> None:
    """
    Test that a Type name containing '#' raises InvalidIdentifierError.

    '#' is reserved for userset notation ("type#relation") inside
    Relation.allowed_subject_types — _schema_validation.py tells the two
    apart by checking for '#' in each entry. If a real Type name could
    also contain '#', a plain-type entry that happened to match one would
    be silently treated as a userset reference instead, skipping the
    TupleToUserset.computed validation entirely. Forbidding '#' in Type
    names makes that ambiguity structurally impossible instead of relying
    on nobody ever naming a type that way.
    """
    with raises(InvalidIdentifierError):
        Type(name="folder#archive", relations={}, permissions={})


def test_type_invalid_relation_key_raises() -> None:
    """
    Test that an InvalidIdentifierError is raised when a relations key is invalid.
    """
    with raises(InvalidIdentifierError):
        Type(name="document", relations={"": Relation(allowed_subject_types=("user",))}, permissions={})


def test_type_invalid_permission_key_raises() -> None:
    """
    Test that an InvalidIdentifierError is raised when a permissions key is invalid.
    """
    with raises(InvalidIdentifierError):
        Type(name="document", relations={}, permissions={"": Reference(name="owner")})


def test_type_relations_become_read_only_view() -> None:
    """
    Test that `relations` is wrapped in a MappingProxyType, blocking item assignment.
    """
    type_ = Type(name="document", relations={"owner": Relation(allowed_subject_types=("user",))}, permissions={})
    assert isinstance(type_.relations, MappingProxyType)

    with raises(TypeError):
        type_.relations["editor"] = Relation(allowed_subject_types=("user",))  # ty: ignore[invalid-assignment]


def test_type_permissions_become_read_only_view() -> None:
    """
    Test that `permissions` is wrapped in a MappingProxyType, blocking item assignment.
    """
    type_ = Type(name="document", relations={}, permissions={"view": Reference(name="owner")})
    assert isinstance(type_.permissions, MappingProxyType)

    with raises(TypeError):
        type_.permissions["edit"] = Reference(name="owner")  # ty: ignore[invalid-assignment]


def test_type_relations_copies_caller_dict() -> None:
    """
    Test that mutating the original dict passed in does not affect the constructed Type.

    `MappingProxyType` is a live view, not a snapshot — wrapping the caller's
    dict directly would let a later mutation of that dict leak through. `Type`
    must wrap a copy instead.
    """
    original = {"owner": Relation(allowed_subject_types=("user",))}
    type_ = Type(name="document", relations=original, permissions={})

    original["editor"] = Relation(allowed_subject_types=("user",))

    assert "editor" not in type_.relations


def test_type_equality() -> None:
    """
    Test that two Type instances with the same fields are equal.
    """
    relations = {"owner": Relation(allowed_subject_types=("user",))}
    assert Type(name="document", relations=relations, permissions={}) == Type(
        name="document", relations=relations, permissions={}
    )


def test_type_inequality_different_name() -> None:
    """
    Test that two Type instances with a different name are not equal.
    """
    assert Type(name="document", relations={}, permissions={}) != Type(name="folder", relations={}, permissions={})


def test_type_inequality_different_relations() -> None:
    """
    Test that two Type instances with different relations are not equal.
    """
    assert Type(name="document", relations={}, permissions={}) != Type(
        name="document",
        relations={"owner": Relation(allowed_subject_types=("user",))},
        permissions={},
    )


def test_type_is_frozen() -> None:
    """
    Test that Type instances cannot be mutated after construction.
    """
    type_ = Type(name="document", relations={}, permissions={})

    with raises(FrozenInstanceError):
        type_.name = "folder"  # ty: ignore[invalid-assignment]

    with raises(FrozenInstanceError):
        type_.relations = {}  # ty: ignore[invalid-assignment]

    with raises(FrozenInstanceError):
        type_.permissions = {}  # ty: ignore[invalid-assignment]


def test_type_not_hashable() -> None:
    """
    Test that Type is not hashable.

    `relations`/`permissions` are `MappingProxyType`, which is itself
    unhashable (it delegates to the wrapped dict). This is accepted:
    neither `Type` nor `CompiledModel` are ever used as a dict key or set
    member anywhere in the design.
    """
    type_ = Type(name="document", relations={}, permissions={})

    with raises(TypeError):
        hash(type_)
