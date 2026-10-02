"""
Base class for all policy pattern errors.
To create a standardized error response, inherit from this class and set the `code` attribute to a unique error code.
"""

from typing import ClassVar


class BaseError(Exception):
    """
    Custom exception class for policy pattern errors.
    It provides a standardized error response format with a unique error code, message,
    and optional related information.
    """

    code: ClassVar[str]

    def __init__(self, *, message: str, related: str | None = None) -> None:
        """
        Initialize the BaseError following the standard error response format in the policy pattern docs errors.md.

        Args:
            message (str): A description of the error.
            related (str | None): Additional information about the error, such as the field or type that caused it.
        """
        self.message = message
        self.related = related
        super().__init__(f"[{self.code}] {message}")
