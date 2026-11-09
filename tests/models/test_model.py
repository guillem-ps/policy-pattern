"""
Test module for the Model class.
"""

from pytest import mark, raises

from policy_pattern.errors import ModelValidationError
from policy_pattern.models import (
    CompiledModel,
    Exclusion,
    Intersection,
    Model,
    PermissionExpression,
    Reference,
    Relation,
    TupleToUserset,
    Type,
    Union,
)


@mark.unit
def test_model_default_construction() -> None:
    """
    Test that a Model constructs with an empty types dict by default.
    """
    model = Model()
    assert model.types == {}


@mark.unit
def test_model_types_is_mutable() -> None:
    """
    Test that `types` can be mutated after construction — Model is authoring-time, not frozen.
    """
    model = Model()
    model.types["document"] = Type(name="document", relations={}, permissions={})
    assert "document" in model.types


@mark.unit
def test_model_equality() -> None:
    """
    Test that two Model instances with the same types are equal.
    """
    types = {"document": Type(name="document", relations={}, permissions={})}
    assert Model(types=dict(types)) == Model(types=dict(types))


@mark.unit
def test_model_inequality_different_types() -> None:
    """
    Test that two Model instances with different types are not equal.
    """
    document = Type(name="document", relations={}, permissions={})
    folder = Type(name="folder", relations={}, permissions={})
    assert Model(types={"document": document}) != Model(types={"folder": folder})


@mark.unit
def test_model_not_hashable() -> None:
    """
    Test that Model is not hashable — it is mutable, so dataclass disables __hash__.
    """
    model = Model()
    with raises(TypeError):
        hash(model)


@mark.unit
def test_model_compile_valid_returns_compiled_model() -> None:
    """
    Test that a valid Model compiles into a CompiledModel with matching content.
    """
    document = Type(
        name="document",
        relations={"owner": Relation(allowed_subject_types=("user",))},
        permissions={"view": Reference(name="owner")},
    )
    model = Model(types={"document": document})

    compiled = model.compile()

    assert isinstance(compiled, CompiledModel)
    assert compiled.types["document"] is document


@mark.unit
def test_model_compile_mismatched_type_name_raises() -> None:
    """
    Test that a Type whose `name` disagrees with its key in `types` raises ModelValidationError.

    The dict key is the identifier actually used for lookups
    (`CompiledModel.types["document"]`) — if `Type.name` disagreed, error
    messages (keyed by `type_name`) would describe a type that isn't the
    one being validated.
    """
    document = Type(name="folder", relations={}, permissions={})
    model = Model(types={"document": document})

    with raises(ModelValidationError) as exc_info:
        model.compile()

    assert exc_info.value.message == "model key 'document' does not match Type.name 'folder'"


@mark.unit
def test_model_compile_undeclared_reference_raises() -> None:
    """
    Test that a Reference to an undeclared name raises ModelValidationError.
    """
    document = Type(
        name="document",
        relations={},
        permissions={"view": Reference(name="missing")},
    )
    model = Model(types={"document": document})

    with raises(ModelValidationError) as exc_info:
        model.compile()

    assert exc_info.value.message == "document.view references undeclared name 'missing'"


@mark.unit
def test_model_compile_tuple_to_userset_target_type_must_be_declared_raises() -> None:
    """
    Test that a tupleset relation's allowed_subject_types must name only declared Types.

    "folder" is a legitimate-looking type name in allowed_subject_types,
    but this model never declares a "folder" Type — computed="viewer"
    could never be checked against it. IMPORTANT (TupleToUserset gap).
    """
    document = Type(
        name="document",
        relations={"parent": Relation(allowed_subject_types=("folder",))},
        permissions={"inherited_viewer": TupleToUserset(tupleset="parent", computed="viewer")},
    )
    model = Model(types={"document": document})

    with raises(ModelValidationError) as exc_info:
        model.compile()

    assert exc_info.value.message == "document.inherited_viewer tupleset 'parent' allows undeclared type 'folder'"


@mark.unit
def test_model_compile_tuple_to_userset_computed_must_exist_on_target_type_raises() -> None:
    """
    Test that TupleToUserset.computed must exist on every plain-type target the tupleset relation allows.

    IMPORTANT (TupleToUserset gap): "does_not_exist" was previously
    accepted by compile() with no check at all, only surfacing later as
    UnknownNameError at check()-time.
    """
    document = Type(
        name="document",
        relations={"parent": Relation(allowed_subject_types=("folder",))},
        permissions={"inherited_viewer": TupleToUserset(tupleset="parent", computed="does_not_exist")},
    )
    folder = Type(name="folder", relations={"viewer": Relation(allowed_subject_types=("user",))}, permissions={})
    model = Model(types={"document": document, "folder": folder})

    with raises(ModelValidationError) as exc_info:
        model.compile()

    assert exc_info.value.message == (
        "document.inherited_viewer computed 'does_not_exist' is not declared as a relation or permission on 'folder'"
    )


@mark.unit
def test_model_compile_tuple_to_userset_ignores_userset_shaped_allowed_subject_type() -> None:
    """
    Test that a userset-shaped allowed_subject_types entry ("type#relation") is never validated as a traversal target.

    _check_tuple_to_userset only ever follows DirectSubject entries, so a
    userset-shaped entry can never actually be the "related object"
    computed is checked against — it must not be required to name a
    declared Type, unlike a plain-type entry.
    """
    document = Type(
        name="document",
        relations={"parent": Relation(allowed_subject_types=("folder", "workspace#member"))},
        permissions={"inherited_viewer": TupleToUserset(tupleset="parent", computed="viewer")},
    )
    folder = Type(name="folder", relations={"viewer": Relation(allowed_subject_types=("user",))}, permissions={})
    model = Model(types={"document": document, "folder": folder})

    compiled = model.compile()

    assert "document" in compiled.types


@mark.unit
def test_model_compile_tupleset_must_be_relation_raises() -> None:
    """
    Test that a TupleToUserset whose tupleset resolves to a permission (not a relation) raises ModelValidationError.
    """
    document = Type(
        name="document",
        relations={"owner": Relation(allowed_subject_types=("user",))},
        permissions={"editor": Reference(name="owner"), "view": TupleToUserset(tupleset="editor", computed="view")},
    )
    model = Model(types={"document": document})

    with raises(ModelValidationError) as exc_info:
        model.compile()

    assert exc_info.value.message == (
        "document.view tupleset 'editor' must be a relation, not a permission or an undeclared name"
    )


@mark.unit
def test_model_compile_valid_tuple_to_userset() -> None:
    """
    Test that a TupleToUserset whose tupleset resolves to a relation compiles without raising.

    Covers the non-raising branch of the tupleset-must-be-relation check —
    the error-path test above only ever exercised the raising side.
    """
    folder = Type(
        name="folder",
        relations={"parent": Relation(allowed_subject_types=("folder",))},
        permissions={"view": TupleToUserset(tupleset="parent", computed="view")},
    )
    model = Model(types={"folder": folder})

    compiled = model.compile()

    assert compiled.types["folder"] is folder


@mark.unit
def test_model_compile_recurses_into_union_and_intersection() -> None:
    """
    Test that compile() recurses into both operands of Union and Intersection.
    """
    document = Type(
        name="document",
        relations={
            "owner": Relation(allowed_subject_types=("user",)),
            "editor": Relation(allowed_subject_types=("user",)),
        },
        permissions={
            "view": Union(left=Reference(name="owner"), right=Reference(name="editor")),
            "manage": Intersection(left=Reference(name="owner"), right=Reference(name="editor")),
        },
    )
    model = Model(types={"document": document})

    compiled = model.compile()

    assert compiled.types["document"] is document


@mark.unit
def test_model_compile_union_propagates_undeclared_right_operand() -> None:
    """
    Test that compile() validates the *right* operand of a Union, not only the left.

    A recursion bug that only checked `.left` would let this silently pass —
    same failure class as the swapped include/exclude bug caught in
    test_operators.py.
    """
    document = Type(
        name="document",
        relations={"owner": Relation(allowed_subject_types=("user",))},
        permissions={"view": Union(left=Reference(name="owner"), right=Reference(name="missing"))},
    )
    model = Model(types={"document": document})

    with raises(ModelValidationError) as exc_info:
        model.compile()

    assert exc_info.value.message == "document.view references undeclared name 'missing'"


@mark.unit
def test_model_compile_exclusion_propagates_undeclared_exclude_operand() -> None:
    """
    Test that compile() validates both `include` and `exclude` operands of an Exclusion.
    """
    document = Type(
        name="document",
        relations={"owner": Relation(allowed_subject_types=("user",))},
        permissions={"view": Exclusion(include=Reference(name="owner"), exclude=Reference(name="missing"))},
    )
    model = Model(types={"document": document})

    with raises(ModelValidationError) as exc_info:
        model.compile()

    assert exc_info.value.message == "document.view references undeclared name 'missing'"


@mark.unit
def test_model_compile_unknown_expression_type_raises() -> None:
    """
    Test that an unrecognized PermissionExpression subtype hits the exhaustiveness fallback.
    """
    document = Type(name="document", relations={}, permissions={"view": PermissionExpression()})
    model = Model(types={"document": document})

    with raises(ModelValidationError) as exc_info:
        model.compile()

    assert exc_info.value.message == "document.view contains unknown expression type 'PermissionExpression'"


@mark.unit
def test_model_compile_rejects_name_used_as_both_relation_and_permission() -> None:
    """
    Test that a name declared as both a relation and a permission on the same Type raises ModelValidationError.

    `Reference`'s own docstring assumes a name is unambiguously either a
    relation or a permission ("the evaluator resolves which one it is at
    evaluation time") — nothing enforced that until now, so this state was
    silently compilable.
    """
    document = Type(
        name="document",
        relations={"owner": Relation(allowed_subject_types=("user",))},
        permissions={"owner": Reference(name="editor"), "editor": Reference(name="owner")},
    )
    model = Model(types={"document": document})

    with raises(ModelValidationError) as exc_info:
        model.compile()

    assert exc_info.value.message == "document declares ['owner'] as both a relation and a permission"
    assert exc_info.value.related == "type='document'"


@mark.unit
def test_model_compile_direct_permission_cycle_raises() -> None:
    """A permission that references itself is rejected during compilation."""
    document = Type(
        name="document",
        relations={"owner": Relation(allowed_subject_types=("user",))},
        permissions={"a": Reference(name="a")},
    )

    with raises(ModelValidationError) as exc_info:
        Model(types={"document": document}).compile()

    assert exc_info.value.message == "document.a references permission cycle to 'a'"


@mark.unit
def test_model_compile_two_permission_cycle_raises() -> None:
    """A cycle spanning two permissions is rejected during compilation."""
    document = Type(
        name="document",
        relations={"owner": Relation(allowed_subject_types=("user",))},
        permissions={"a": Reference(name="b"), "b": Reference(name="a")},
    )

    with raises(ModelValidationError, match="cycle"):
        Model(types={"document": document}).compile()


@mark.unit
def test_model_compile_permission_cycle_in_union_raises() -> None:
    """A cyclic permission reference in either Union branch is rejected."""
    document = Type(
        name="document",
        relations={"owner": Relation(allowed_subject_types=("user",))},
        permissions={"a": Union(left=Reference(name="owner"), right=Reference(name="b")), "b": Reference(name="a")},
    )

    with raises(ModelValidationError, match="cycle"):
        Model(types={"document": document}).compile()


@mark.unit
def test_model_compile_permission_cycle_in_exclusion_raises() -> None:
    """A cyclic permission reference in an Exclusion operand is rejected."""
    document = Type(
        name="document",
        relations={"owner": Relation(allowed_subject_types=("user",))},
        permissions={
            "a": Exclusion(include=Reference(name="owner"), exclude=Reference(name="b")),
            "b": Reference(name="a"),
        },
    )

    with raises(ModelValidationError, match="cycle"):
        Model(types={"document": document}).compile()


@mark.unit
def test_model_compile_long_acyclic_permission_chain() -> None:
    """A long permission chain ending at a relation compiles successfully."""
    document = Type(
        name="document",
        relations={"owner": Relation(allowed_subject_types=("user",))},
        permissions={"a": Reference(name="b"), "b": Reference(name="c"), "c": Reference(name="owner")},
    )

    assert Model(types={"document": document}).compile().types["document"] is document


@mark.unit
def test_model_compile_tuple_to_userset_computed_name_is_not_static_cycle() -> None:
    """TupleToUserset computed names are not same-object static permission edges."""
    document = Type(
        name="document",
        relations={
            "owner": Relation(allowed_subject_types=("user",)),
            "parent": Relation(allowed_subject_types=("folder",)),
        },
        permissions={
            "a": Union(
                left=Reference(name="owner"),
                right=TupleToUserset(tupleset="parent", computed="a"),
            )
        },
    )
    folder = Type(
        name="folder",
        relations={"owner": Relation(allowed_subject_types=("user",))},
        permissions={"a": Reference(name="owner")},
    )

    assert Model(types={"document": document, "folder": folder}).compile().types["document"] is document
