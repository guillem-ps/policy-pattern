"""
Value Object representing an immutable, validated authorization schema.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType  # Immutable dict wrapper

from ._schema_validation import validate_types
from .type import Type


@dataclass(frozen=True, slots=True)
class CompiledModel:
    """
    Immutable, validated result of `Model.compile()` — the only thing `Evaluator` accepts.

    The intended path is always `Model.compile()`, but Python has no real
    private constructor — calling `CompiledModel(types=...)` directly is
    possible. `__post_init__` re-runs `validate_types()`, the same check
    `Model.compile()` relies on, so a direct call can never hand the
    `Evaluator` an object holding an undeclared `Reference`, a `tupleset`
    resolving to a permission, or a mismatched type name — it either
    produces the same result `compile()` would have, or raises the same
    `ModelValidationError`.

    `types` is wrapped in `MappingProxyType` on construction — a mutable
    `dict` field would let that guarantee be violated after the fact
    (`compiled.types["x"] = Type(...)` sneaking an unvalidated `Type` past
    validation entirely).

    Example:
        compiled = model.compile()
    """

    types: Mapping[str, Type]

    def __post_init__(self) -> None:
        """
        Validates `types`, then makes it a read-only view over a copy of the input mapping.
        """
        validate_types(self.types)
        object.__setattr__(self, "types", MappingProxyType(dict(self.types)))
