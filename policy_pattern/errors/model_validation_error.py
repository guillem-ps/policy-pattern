"""
Set of errors related to Model validation at compile() time.
"""

from .base_error import BaseError


class ModelValidationError(BaseError):
    """
    Error raised when a Model fails compile()-time validation.
    Attributes:
        code (ClassVar[str]): A unique error code for the specific error type.
    """

    code = "PP101"
