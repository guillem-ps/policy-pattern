"""
Standalone probe for tests/test_evaluator.py's userset-expansion determinism check.

Never imported directly — invoked via subprocess with different
PYTHONHASHSEED values, so its stdout can be compared across processes.
"""

from policy_pattern.adapters.memory import MemoryTupleStore
from policy_pattern.errors import EvaluationError
from policy_pattern.evaluator import Evaluator
from policy_pattern.models import (
    CompiledModel,
    DirectSubject,
    Mutation,
    ObjectReference,
    Relation,
    SubjectSet,
    Tuple,
    Type,
)

model = CompiledModel(
    types={
        "group": Type(
            name="group",
            relations={"member": Relation(allowed_subject_types=("user", "group#member"))},
            permissions={},
        ),
    }
)
store = MemoryTupleStore()
alice = DirectSubject(object=ObjectReference(type="user", id="alice"))
group_a = ObjectReference(type="group", id="a")
group_c = ObjectReference(type="group", id="c")

store.write_tuples(
    Mutation(
        additions=frozenset(
            {
                # self-referencing branch: following it re-enters (group:a, "member"), already in progress -> cycle
                Tuple(subject=SubjectSet(object=group_a, relation="member"), relation="member", object=group_a),
                # genuine branch: alice really is a member of group:c
                Tuple(subject=SubjectSet(object=group_c, relation="member"), relation="member", object=group_a),
                Tuple(subject=alice, relation="member", object=group_c),
            }
        ),
        deletions=frozenset(),
    )
)

evaluator = Evaluator(model=model, store=store)
try:
    print(evaluator.check(alice, "member", group_a))
except EvaluationError as error:
    print(f"EvaluationError: {error.message}")
