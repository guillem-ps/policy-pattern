"""
Set of errors related to referencing a relation/permission name not declared on a type.
"""

from .base_error import BaseError


class UnknownNameError(BaseError):
    """
    Error raised when check() references a name that is declared as neither a relation
    nor a permission on the object's (already-known) type.
    Attributes:
        code (ClassVar[str]): A unique error code for the specific error type.
    """

    code = "PP005"
