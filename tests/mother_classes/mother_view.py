"""
Mother class for building test View instances.
"""

from typing import override

from policy_pattern.models import Subject
from policy_pattern.ports import ReadResult, View


class MotherView(View):
    """
    Minimal View test double — every read reports "nothing found, complete" by default.
    """

    @override
    def read_tuple(self, subject, relation, object) -> bool:  # noqa: ANN001
        """
        Always reports the tuple as absent.
        """
        return False

    @override
    def read_relation(self, object, relation, limit) -> ReadResult:  # noqa: ANN001
        """
        Always reports an empty, complete result.
        """
        return ReadResult(tuples=frozenset(), complete=True)

    @override
    def read_tuples_for_subject(self, subject: Subject, limit: int) -> ReadResult:
        """Always reports an empty, complete result."""
        return ReadResult(tuples=frozenset(), complete=True)
