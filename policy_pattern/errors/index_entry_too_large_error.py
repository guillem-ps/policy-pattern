"""
Set of errors related to storage adapters rejecting an oversized index entry.
"""

from .base_error import BaseError


class IndexEntryTooLargeError(BaseError):
    """
    Error raised when a tuple's encoded primary key would exceed a storage
    backend's index entry size limit.
    Attributes:
        code (ClassVar[str]): A unique error code for the specific error type.
    """

    code = "PP900"
