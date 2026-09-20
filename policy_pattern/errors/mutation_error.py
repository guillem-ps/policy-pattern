"""
Set of errors related to Mutation class.
"""

from .base_error import BaseError


class InvalidMutationError(BaseError):
    """
    Error raised when an invalid mutation is encountered.
    Attributes:
        code (ClassVar[str]): A unique error code for the specific error type.
    """

    code = "PP003"
