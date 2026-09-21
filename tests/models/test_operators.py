"""
Tests for the operator methods in the PermissionExpression class.
And the resulting classes Union, Intersection, and Exclusion.
"""

from policy_pattern.models import Exclusion, Intersection, PermissionExpression, Union


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
