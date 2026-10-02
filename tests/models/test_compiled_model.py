"""
Test module for the CompiledModel class.
"""

from dataclasses import FrozenInstanceError
from types import MappingProxyType

from pytest import raises

from policy_pattern.errors import ModelValidationError
from policy_pattern.models import CompiledModel, Reference, Type


def test_compiled_model_valid_construction() -> None:
    """
    Test that a valid CompiledModel can be constructed without raising an error.
    """
    document = Type(name="document", relations={}, permissions={})
    compiled = CompiledModel(types={"document": document})
    assert compiled.types["document"] is document


def test_compiled_model_direct_construction_validates_undeclared_reference() -> None:
    """
    Test that constructing CompiledModel directly (bypassing Model.compile()) still validates.

    `CompiledModel`'s docstring says `Evaluator` trusts it as already
    validated — without this guard, a caller who skips `Model.compile()`
    could hand the evaluator an undeclared `Reference` past that trust
    boundary entirely.
    """
    document = Type(name="document", relations={}, permissions={"view": Reference(name="missing")})

    with raises(ModelValidationError) as exc_info:
        CompiledModel(types={"document": document})

    assert exc_info.value.message == "document.view references undeclared name 'missing'"


def test_compiled_model_direct_construction_validates_mismatched_type_name() -> None:
    """
    Test that constructing CompiledModel directly still validates the key/name match.
    """
    document = Type(name="folder", relations={}, permissions={})

    with raises(ModelValidationError) as exc_info:
        CompiledModel(types={"document": document})

    assert exc_info.value.message == "model key 'document' does not match Type.name 'folder'"


def test_compiled_model_types_become_read_only_view() -> None:
    """
    Test that `types` is wrapped in a MappingProxyType, blocking item assignment.
    """
    compiled = CompiledModel(types={"document": Type(name="document", relations={}, permissions={})})
    assert isinstance(compiled.types, MappingProxyType)

    with raises(TypeError):
        compiled.types["folder"] = Type(name="folder", relations={}, permissions={})  # ty: ignore[invalid-assignment]


def test_compiled_model_copies_caller_dict() -> None:
    """
    Test that mutating the original dict passed in does not affect the constructed CompiledModel.
    """
    document = Type(name="document", relations={}, permissions={})
    original = {"document": document}
    compiled = CompiledModel(types=original)

    original["folder"] = Type(name="folder", relations={}, permissions={})

    assert "folder" not in compiled.types


def test_compiled_model_equality() -> None:
    """
    Test that two CompiledModel instances with the same types are equal.
    """
    types = {"document": Type(name="document", relations={}, permissions={})}
    assert CompiledModel(types=types) == CompiledModel(types=types)


def test_compiled_model_inequality_different_types() -> None:
    """
    Test that two CompiledModel instances with different types are not equal.
    """
    document = Type(name="document", relations={}, permissions={})
    folder = Type(name="folder", relations={}, permissions={})
    assert CompiledModel(types={"document": document}) != CompiledModel(types={"folder": folder})


def test_compiled_model_is_frozen() -> None:
    """
    Test that CompiledModel instances cannot be mutated after construction.
    """
    compiled = CompiledModel(types={})

    with raises(FrozenInstanceError):
        compiled.types = {}  # ty: ignore[invalid-assignment]


def test_compiled_model_not_hashable() -> None:
    """
    Test that CompiledModel is not hashable.

    `types` is a `MappingProxyType`, which is itself unhashable. Accepted:
    `CompiledModel` is never used as a dict key or set member.
    """
    with raises(TypeError):
        hash(CompiledModel(types={}))
