"""
Shared schema validation for `Model.compile()` and `CompiledModel` construction.
"""

from collections.abc import Mapping

from policy_pattern.errors import ModelValidationError

from .operators import Exclusion, Intersection, PermissionExpression, Union
from .reference import Reference
from .tuple_to_userset import TupleToUserset
from .type import Type


def validate_types(types: Mapping[str, Type]) -> None:
    """
    Validates every Type's key against its own name, and every Reference/tupleset it declares.

    Lives in its own module, not inside `Model` or `CompiledModel`, so both
    can call the exact same check — `Model.compile()` on the normal path,
    `CompiledModel.__post_init__` against a direct construction that
    bypassed it. One validator, not two copies that can drift apart.

    Raises:
        ModelValidationError: If a `Type`'s key doesn't match its own `name`,
            a `Reference`/`tupleset` name doesn't exist on its own type, or a
            `tupleset` resolves to a permission instead of a relation.

        ModelValidationError: If a permission expression and relation share the same name on the same type,
        which is illegal.
    """
    for type_name, type_declaration in types.items():
        if type_name != type_declaration.name:
            raise ModelValidationError(
                message=f"model key {type_name!r} does not match Type.name {type_declaration.name!r}",
                related=f"type={type_name!r}",
            )
        if overlap := sorted(type_declaration.relations.keys() & type_declaration.permissions.keys()):
            raise ModelValidationError(
                message=f"{type_name} declares {overlap!r} as both a relation and a permission",
                related=f"type={type_name!r}",
            )

        for permission_name, expression in type_declaration.permissions.items():
            _validate_expression(expression, type_declaration, type_name, permission_name)


def _validate_expression(
    expression: PermissionExpression,
    type_declaration: Type,
    type_name: str,
    permission_name: str,
) -> None:
    """
    Recursively validates one permission expression against its own type's declarations.
    """
    if isinstance(expression, Reference):
        # Leaf: name must resolve within this type's own namespace.
        known = type_declaration.relations.keys() | type_declaration.permissions.keys()
        if expression.name not in known:
            raise ModelValidationError(
                message=f"{type_name}.{permission_name} references undeclared name {expression.name!r}",
                related=f"type={type_name!r}",
            )
    elif isinstance(expression, TupleToUserset):
        # Leaf: tupleset must be a stored edge — nothing to traverse if it were computed.
        if expression.tupleset not in type_declaration.relations:
            raise ModelValidationError(
                message=(
                    f"{type_name}.{permission_name} tupleset {expression.tupleset!r} "
                    "must be a relation, not a permission or an undeclared name"
                ),
                related=f"type={type_name!r}",
            )
    elif isinstance(expression, (Union, Intersection)):
        # Rewrite combinator: set-algebra, commutative — validate both operands, order doesn't matter.
        _validate_expression(expression.left, type_declaration, type_name, permission_name)
        _validate_expression(expression.right, type_declaration, type_name, permission_name)
    elif isinstance(expression, Exclusion):
        # Rewrite combinator, not commutative — include/exclude both required; skipping one is the
        # classic false-allow bug (an accidental swap would silently invert the exclusion).
        _validate_expression(expression.include, type_declaration, type_name, permission_name)
        _validate_expression(expression.exclude, type_declaration, type_name, permission_name)
    else:
        raise ModelValidationError(
            message=f"{type_name}.{permission_name} contains unknown expression type {type(expression).__name__}",
            related=f"type={type_name!r}",
        )
