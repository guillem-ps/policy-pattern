"""
Set of errors related to Relation class.
"""

from .base_error import BaseError


class InvalidRelationError(BaseError):
    """
    Error raised when an invalid relation is encountered.
    Attributes:
        code (ClassVar[str]): A unique error code for the specific error type.
    """

    code = "PP002"
