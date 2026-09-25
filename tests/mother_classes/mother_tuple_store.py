"""
Mother class for building test TupleStore instances.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import override

from policy_pattern.models import Mutation
from policy_pattern.ports import TupleStore, View

from .mother_view import MotherView


class MotherTupleStore(TupleStore):
    """
    Minimal TupleStore test double — records the last mutation passed to write_tuples().
    """

    def __init__(self) -> None:
        """
        Initializes with no mutation received yet.
        """
        self.received_mutation: Mutation | None = None

    @override
    def write_tuples(self, mutation: Mutation) -> None:
        """
        Records the mutation instead of applying it anywhere.
        """
        self.received_mutation = mutation

    @override
    @contextmanager
    def snapshot(self) -> Generator[View, None, None]:
        """
        Yields a fresh MotherView.
        """
        yield MotherView()
