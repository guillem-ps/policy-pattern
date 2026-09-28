"""
Set of errors related to Evaluator runtime failures (budget exceeded, cycle detected).
"""

from .base_error import BaseError


class EvaluationError(BaseError):
    """
    Error raised when check() cannot complete: a cycle was detected, or a configured
    EvaluationBudget limit (max_depth, max_nodes, max_store_reads) was exceeded.
    Attributes:
        code (ClassVar[str]): A unique error code for the specific error type.
    """

    code = "PP201"
