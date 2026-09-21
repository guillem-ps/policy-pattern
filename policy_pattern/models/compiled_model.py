"""
Value Object representing an immutable, validated authorization schema.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType  # Inmutables dict wrapper

from .type import Type


@dataclass(frozen=True, slots=True)
class CompiledModel:
    """
    Immutable result of `Model.compile()` — the only thing `Evaluator` accepts.

    Never constructed directly: the only way to get one is a successful
    `Model.compile()`, which means every `Reference`/`tupleset` name has
    already been validated. There is no `__post_init__` here re-checking
    that — `compile()` already did it; `CompiledModel` just carries the
    result forward as a distinct, "already validated" type.

    `types` is wrapped in `MappingProxyType` on construction — this is the
    one class in the package where that actually matters most: `Evaluator`
    trusts a `CompiledModel` is exactly what `compile()` validated, and a
    mutable `dict` field would let that trust be violated after the fact
    (`compiled.types["x"] = Type(...)` sneaking an unvalidated `Type` past
    `compile()` entirely).

    Example:
        compiled = model.compile()
    """

    types: Mapping[str, Type]

    def __post_init__(self) -> None:
        """
        Makes `types` a read-only view over a copy of the input mapping.
        """
        object.__setattr__(self, "types", MappingProxyType(dict(self.types)))
