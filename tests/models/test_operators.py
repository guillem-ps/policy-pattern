"""
Tests for the operator methods in the PermissionExpression class.
And the resulting classes Union, Intersection, and Exclusion.
"""

from dataclasses import FrozenInstanceError

from pytest import mark, raises

from policy_pattern.models import Exclusion, Intersection, PermissionExpression, Reference, Union


@mark.unit
def test_or_method_return_union() -> None:
    """
    Test that the `__or__` method returns a new PermissionExpression representing the union of two expressions.
    """
    expr1 = PermissionExpression()
    expr2 = PermissionExpression()
    union_expr = expr1 | expr2

    assert isinstance(union_expr, Union)
    assert union_expr.left is expr1
    assert union_expr.right is expr2


@mark.unit
def test_and_method_return_intersection() -> None:
    """
    Test that the `__and__` method returns a new PermissionExpression representing the intersection of two expressions.
    """
    expr1 = PermissionExpression()
    expr2 = PermissionExpression()
    intersection_expr = expr1 & expr2

    assert isinstance(intersection_expr, Intersection)
    assert intersection_expr.left is expr1
    assert intersection_expr.right is expr2


@mark.unit
def test_sub_method_return_exclusion() -> None:
    """
    Test that the `__sub__` method returns a new PermissionExpression representing the exclusion of two expressions.
    """
    expr1 = PermissionExpression()
    expr2 = PermissionExpression()
    exclusion_expr = expr1 - expr2

    assert isinstance(exclusion_expr, Exclusion)
    assert exclusion_expr.include is expr1
    assert exclusion_expr.exclude is expr2


@mark.unit
def test_union_equality() -> None:
    """
    Test that two Union instances with the same left and right are equal.
    """
    assert Union(left=Reference(name="owner"), right=Reference(name="editor")) == Union(
        left=Reference(name="owner"), right=Reference(name="editor")
    )


@mark.unit
def test_union_inequality_different_left() -> None:
    """
    Test that two Union instances with a different left are not equal.
    """
    assert Union(left=Reference(name="owner"), right=Reference(name="editor")) != Union(
        left=Reference(name="viewer"), right=Reference(name="editor")
    )


@mark.unit
def test_union_inequality_different_right() -> None:
    """
    Test that two Union instances with a different right are not equal.
    """
    assert Union(left=Reference(name="owner"), right=Reference(name="editor")) != Union(
        left=Reference(name="owner"), right=Reference(name="viewer")
    )


@mark.unit
def test_union_hash_consistency() -> None:
    """
    Test that equal Union instances have the same hash value.
    """
    assert hash(Union(left=Reference(name="owner"), right=Reference(name="editor"))) == hash(
        Union(left=Reference(name="owner"), right=Reference(name="editor"))
    )


@mark.unit
def test_union_is_frozen() -> None:
    """
    Test that Union instances cannot be mutated after construction.
    """
    union = Union(left=Reference(name="owner"), right=Reference(name="editor"))

    with raises(FrozenInstanceError):
        union.left = Reference(name="viewer")  # ty: ignore[invalid-assignment]

    with raises(FrozenInstanceError):
        union.right = Reference(name="viewer")  # ty: ignore[invalid-assignment]


@mark.unit
def test_intersection_equality() -> None:
    """
    Test that two Intersection instances with the same left and right are equal.
    """
    assert Intersection(left=Reference(name="editor"), right=Reference(name="active_member")) == Intersection(
        left=Reference(name="editor"), right=Reference(name="active_member")
    )


@mark.unit
def test_intersection_inequality_different_left() -> None:
    """
    Test that two Intersection instances with a different left are not equal.
    """
    assert Intersection(left=Reference(name="editor"), right=Reference(name="active_member")) != Intersection(
        left=Reference(name="viewer"), right=Reference(name="active_member")
    )


@mark.unit
def test_intersection_inequality_different_right() -> None:
    """
    Test that two Intersection instances with a different right are not equal.
    """
    assert Intersection(left=Reference(name="editor"), right=Reference(name="active_member")) != Intersection(
        left=Reference(name="editor"), right=Reference(name="viewer")
    )


@mark.unit
def test_intersection_hash_consistency() -> None:
    """
    Test that equal Intersection instances have the same hash value.
    """
    assert hash(Intersection(left=Reference(name="editor"), right=Reference(name="active_member"))) == hash(
        Intersection(left=Reference(name="editor"), right=Reference(name="active_member"))
    )


@mark.unit
def test_intersection_is_frozen() -> None:
    """
    Test that Intersection instances cannot be mutated after construction.
    """
    intersection = Intersection(left=Reference(name="editor"), right=Reference(name="active_member"))

    with raises(FrozenInstanceError):
        intersection.left = Reference(name="viewer")  # ty: ignore[invalid-assignment]

    with raises(FrozenInstanceError):
        intersection.right = Reference(name="viewer")  # ty: ignore[invalid-assignment]


@mark.unit
def test_exclusion_equality() -> None:
    """
    Test that two Exclusion instances with the same include and exclude are equal.
    """
    assert Exclusion(include=Reference(name="member"), exclude=Reference(name="blocked")) == Exclusion(
        include=Reference(name="member"), exclude=Reference(name="blocked")
    )


@mark.unit
def test_exclusion_inequality_different_include() -> None:
    """
    Test that two Exclusion instances with a different include are not equal.
    """
    assert Exclusion(include=Reference(name="member"), exclude=Reference(name="blocked")) != Exclusion(
        include=Reference(name="viewer"), exclude=Reference(name="blocked")
    )


@mark.unit
def test_exclusion_inequality_different_exclude() -> None:
    """
    Test that two Exclusion instances with a different exclude are not equal.
    """
    assert Exclusion(include=Reference(name="member"), exclude=Reference(name="blocked")) != Exclusion(
        include=Reference(name="member"), exclude=Reference(name="viewer")
    )


@mark.unit
def test_exclusion_hash_consistency() -> None:
    """
    Test that equal Exclusion instances have the same hash value.
    """
    assert hash(Exclusion(include=Reference(name="member"), exclude=Reference(name="blocked"))) == hash(
        Exclusion(include=Reference(name="member"), exclude=Reference(name="blocked"))
    )


@mark.unit
def test_exclusion_is_frozen() -> None:
    """
    Test that Exclusion instances cannot be mutated after construction.
    """
    exclusion = Exclusion(include=Reference(name="member"), exclude=Reference(name="blocked"))

    with raises(FrozenInstanceError):
        exclusion.include = Reference(name="viewer")  # ty: ignore[invalid-assignment]

    with raises(FrozenInstanceError):
        exclusion.exclude = Reference(name="viewer")  # ty: ignore[invalid-assignment]
