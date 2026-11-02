"""Security invariant tests for both list_objects() candidate sources."""

from pytest import mark

from policy_pattern.evaluator import Evaluator
from policy_pattern.models import (
    CompiledModel,
    DirectSubject,
    Mutation,
    ObjectReference,
    Reference,
    Relation,
    SubjectSet,
    Tuple,
    TupleToUserset,
    Type,
    Union,
)
from policy_pattern.ports import TupleStore

SUBJECT = DirectSubject(object=ObjectReference(type="user", id="alice"))


def _fixture_set() -> tuple[CompiledModel, frozenset[Tuple]]:
    """Build a deterministic mix of direct, group, and parent-linked grants."""
    model = CompiledModel(
        types={
            "group": Type(
                name="group",
                relations={"member": Relation(allowed_subject_types=("user", "group#member"))},
                permissions={},
            ),
            "folder": Type(
                name="folder",
                relations={"viewer": Relation(allowed_subject_types=("user", "group#member"))},
                permissions={},
            ),
            "document": Type(
                name="document",
                relations={
                    "owner": Relation(allowed_subject_types=("user", "group#member")),
                    "parent": Relation(allowed_subject_types=("folder",)),
                },
                permissions={
                    "viewer": Union(
                        left=Reference(name="owner"),
                        right=TupleToUserset(tupleset="parent", computed="viewer"),
                    )
                },
            ),
        }
    )
    group = ObjectReference(type="group", id="engineering")
    folder = ObjectReference(type="folder", id="shared")
    doc_direct = ObjectReference(type="document", id="direct")
    doc_group = ObjectReference(type="document", id="group")
    doc_parent = ObjectReference(type="document", id="parent")
    doc_denied = ObjectReference(type="document", id="denied")
    tuples = frozenset(
        {
            Tuple(subject=SUBJECT, relation="member", object=group),
            Tuple(subject=SUBJECT, relation="owner", object=doc_direct),
            Tuple(subject=SubjectSet(object=group, relation="member"), relation="owner", object=doc_group),
            Tuple(subject=SUBJECT, relation="viewer", object=folder),
            Tuple(subject=DirectSubject(object=folder), relation="parent", object=doc_parent),
            Tuple(
                subject=DirectSubject(object=ObjectReference(type="user", id="bob")),
                relation="owner",
                object=doc_denied,
            ),
        }
    )
    return model, tuples


@mark.contract
def test_list_objects_never_returns_a_false_positive(store: TupleStore) -> None:
    """Every object list_objects() returns, check() independently agrees on."""
    model, tuples = _fixture_set()
    store.write_tuples(Mutation(additions=tuples, deletions=frozenset()))
    evaluator = Evaluator(model=model, store=store)

    returned = evaluator.list_objects(SUBJECT, "viewer", "document")

    assert all(evaluator.check(SUBJECT, "viewer", obj) for obj in returned)
    assert len(returned) > 0


@mark.contract
def test_list_objects_never_returns_a_false_positive_with_candidate_ids(store: TupleStore) -> None:
    """The D7 candidate_ids path uses the same forward-check security filter."""
    model, tuples = _fixture_set()
    store.write_tuples(Mutation(additions=tuples, deletions=frozenset()))
    evaluator = Evaluator(model=model, store=store)
    all_object_ids = frozenset(t.object for t in tuples if t.object.type == "document")

    returned = evaluator.list_objects(SUBJECT, "viewer", "document", candidate_ids=all_object_ids)

    assert all(evaluator.check(SUBJECT, "viewer", obj) for obj in returned)
    assert len(returned) > 0
