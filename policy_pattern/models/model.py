"""
Value Object representing the whole authorization schema.
"""

from dataclasses import dataclass, field

from policy_pattern.errors import ModelValidationError

from .compiled_model import CompiledModel
from .operators import Exclusion, Intersection, PermissionExpression, Union
from .reference import Reference
from .tuple_to_userset import TupleToUserset
from .type import Type


@dataclass(slots=True)
class Model:
    """
    The whole authorization schema — a mutable, authoring-time collection of `Type` declarations.

    Unlike every other class in this package, `Model` is deliberately **not**
    frozen. `architecture.md` already says why: "mutable, authoring-time" —
    it exists to be built up incrementally (`model.types["document"] =
    Type(...)`) before `.compile()` produces the immutable `CompiledModel`
    that `Evaluator` actually accepts. There is no `check()` here, only
    `compile()` — evaluating a bare `Model` is an illegal state the type
    system doesn't even offer a method for.

    Example:
        model = Model()
        model.types["document"] = Type(name="document", relations={...}, permissions={...})
        compiled = model.compile()
    """

    types: dict[str, Type] = field(default_factory=dict[str, Type])

    def compile(self) -> CompiledModel:
        """
        Validates every Reference/tupleset name and returns an immutable CompiledModel.

        Raises:
            ModelValidationError: If a `Reference`/`tupleset` name doesn't exist
                on its own type, or a `tupleset` resolves to a permission instead
                of a relation.
        """
        for type_name, type_declaration in self.types.items():
            for permission_name, expression in type_declaration.permissions.items():
                self._validate_expression(expression, type_declaration, type_name, permission_name)

        return CompiledModel(types=dict(self.types))

    def _validate_expression(
        self,
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
            self._validate_expression(expression.left, type_declaration, type_name, permission_name)
            self._validate_expression(expression.right, type_declaration, type_name, permission_name)
        elif isinstance(expression, Exclusion):
            # Rewrite combinator, not commutative — include/exclude both required; skipping one is the
            # classic false-allow bug (an accidental swap would silently invert the exclusion).
            self._validate_expression(expression.include, type_declaration, type_name, permission_name)
            self._validate_expression(expression.exclude, type_declaration, type_name, permission_name)
        else:
            raise ModelValidationError(
                message=f"{type_name}.{permission_name} contains unknown expression type {type(expression).__name__}",
                related=f"type={type_name!r}",
            )
