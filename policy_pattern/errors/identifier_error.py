"""
Set of errors related with Identifier class.
"""

from .base_error import BaseError


class InvalidIdentifierError(BaseError):
    """
    Error raised when an invalid identifier is encountered.
    Attributes:
        code (ClassVar[str]): A unique error code for the specific error type.
    """

    code = "PP001"
