"""
Standalone probe for tests/adapters/test_memory.py's determinism check.

Never imported directly — invoked via subprocess with different
PYTHONHASHSEED values, so its stdout can be compared across processes.
"""

from policy_pattern.adapters.memory import MemoryTupleStore
from policy_pattern.models import DirectSubject, Mutation, ObjectReference, Tuple


def _make_tuple(id_: str) -> Tuple:
    return Tuple(
        subject=DirectSubject(object=ObjectReference(type="user", id=id_)),
        relation="owner",
        object=ObjectReference(type="document", id="42"),
    )


store = MemoryTupleStore()
tuples = frozenset(_make_tuple(name) for name in ("alice", "bob", "carol", "dave", "eve"))
store.write_tuples(Mutation(additions=tuples, deletions=frozenset()))

with store.snapshot() as view:
    result = view.read_relation(ObjectReference(type="document", id="42"), "owner", limit=3)

print(sorted(t.subject.object.id for t in result.tuples))
