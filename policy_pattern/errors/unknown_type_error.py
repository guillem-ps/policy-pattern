"""
Set of errors related to referencing a type the CompiledModel does not declare.
"""

from .base_error import BaseError


class UnknownTypeError(BaseError):
    """
    Error raised when check() (or internal userset-expansion recursion) references an
    ObjectReference whose type is not declared in the CompiledModel.
    Attributes:
        code (ClassVar[str]): A unique error code for the specific error type.
    """

    code = "PP004"
