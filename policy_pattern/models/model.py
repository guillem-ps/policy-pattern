"""
Value Object representing the whole authorization schema.
"""

from dataclasses import dataclass, field

from .compiled_model import CompiledModel
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
        Returns an immutable, validated CompiledModel.

        Validation itself lives in `CompiledModel.__post_init__`, not here —
        the only way both this normal path and a direct `CompiledModel(...)`
        call get the same guarantee. See `CompiledModel`'s docstring.

        Raises:
            ModelValidationError: If a `Type`'s key in `types` doesn't match
                its own `name`, a `Reference`/`tupleset` name doesn't exist
                on its own type, or a `tupleset` resolves to a permission
                instead of a relation.
        """
        return CompiledModel(types=dict(self.types))
