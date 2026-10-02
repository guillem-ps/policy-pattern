"""
Base class and node types for computed permission expressions.
"""

from __future__ import annotations

from dataclasses import dataclass


class PermissionExpression:
    r"""
    Base class for a computed permission expression — never storable.

    A `Relation` is a stored fact (`document:42#owner@user:john` can exist
    as a `Tuple`). A `Permission` is the opposite: a *rule* for combining
    relations/other permissions, computed at evaluation time, never
    written to the store. `PermissionExpression` is the AST of that rule —
    the same set-theory operations Zanzibar's `userset rewrite` describes,
    expressed as data instead of prose:

        - viewer(o) = owner(o) ∪ editor(o)                Union
        - can_edit(o) = editor(o) ∩ active_member(o)      Intersection
        - viewer(o) = member(o) \ blocked(o)             Exclusion

    Composed via real Python operators instead of nested constructor
    calls — an operator-overloaded composite, not named factory methods:

        viewer = Reference(name="owner") | (
            Reference(name="member") - Reference(name="blocked")
        )

    `__or__`/`__and__`/`__sub__` return new `PermissionExpression` nodes;
    they never mutate `self` — every node here is frozen, an expression
    tree is built bottom-up once and never changes shape afterward.
    """  # noqa: D301, RUF002

    __slots__ = ()

    def __or__(self, other: PermissionExpression) -> Union:
        """
        Combine with `other` as a Union — true if either side is true.
        """
        return Union(left=self, right=other)

    def __and__(self, other: PermissionExpression) -> Intersection:
        """
        Combine with `other` as an Intersection — true only if both sides are true.
        """
        return Intersection(left=self, right=other)

    def __sub__(self, other: PermissionExpression) -> Exclusion:
        """
        Combine with `other` as an Exclusion — true if `self` is true and `other` is false.
        """
        return Exclusion(include=self, exclude=other)


@dataclass(frozen=True, slots=True)
class Union(PermissionExpression):
    """
    Union of two permission expressions — true if either side is true.

    `viewer = owner | editor`: a subject only needs to satisfy one branch,
    not both. The evaluator is free to short-circuit here (stop as soon as
    one side is `True`) — unlike `Exclusion`, a `Union` has no case where
    an error on the untaken branch could hide a false allow.

    Example:
        Union(left=Reference(name="owner"), right=Reference(name="editor"))
    """

    left: PermissionExpression
    right: PermissionExpression


@dataclass(frozen=True, slots=True)
class Intersection(PermissionExpression):
    """
    Intersection of two permission expressions — true only if both sides are true.

    `can_edit = editor & active_member`: a subject must satisfy both
    branches. Unlike `Union`, the evaluator can short-circuit on the first
    `False` branch — a `False` on either side is enough to decide the
    whole node is `False`, regardless of what the other side would have
    evaluated to.

    Example:
        Intersection(left=Reference(name="editor"), right=Reference(name="active_member"))
    """

    left: PermissionExpression
    right: PermissionExpression


@dataclass(frozen=True, slots=True)
class Exclusion(PermissionExpression):
    """
    Set difference: true if `include` is true and `exclude` is false.

    `viewer = member - blocked`: the one node the evaluator must *never*
    short-circuit. If evaluating `exclude` fails (a storage error, a
    cycle, a budget overrun) while `include` is already known to be
    `False`, that failure still has to propagate — treating the failed
    `exclude` as "assume False" would compute `False - False = True`, a
    false allow manufactured entirely out of an evaluation failure on the
    branch that was never actually checked. This is `docs/semantics.md`'s
    "storage errors are not empty results" rule, restated as an evaluation
    rule instead of a storage one: both sides are always evaluated,
    unconditionally.

    Example:
        Exclusion(include=Reference(name="member"), exclude=Reference(name="blocked"))
    """

    include: PermissionExpression
    exclude: PermissionExpression
