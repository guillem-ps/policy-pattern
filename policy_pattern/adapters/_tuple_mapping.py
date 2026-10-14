"""
Data decomposition and recomposition functions for the TupleStore adapters.
"""

from policy_pattern.models import DirectSubject, ObjectReference, Subject, SubjectSet, Tuple


def columns(t: Tuple) -> tuple[str, str, str, str, str, str]:
    """
    Decomposes a Tuple into the six column values this adapter stores.
    """
    if isinstance(t.subject, DirectSubject):
        subject_type, subject_id, subject_relation = t.subject.object.type, t.subject.object.id, ""
    else:
        subject_type, subject_id, subject_relation = (
            t.subject.object.type,
            t.subject.object.id,
            t.subject.relation,
        )
    return (t.object.type, t.object.id, t.relation, subject_type, subject_id, subject_relation)


def decompose(subject: Subject) -> tuple[str, str, str]:
    """
    Decomposes a Subject into (subject_type, subject_id, subject_relation).
    """
    if isinstance(subject, DirectSubject):
        return (subject.object.type, subject.object.id, "")

    return (subject.object.type, subject.object.id, subject.relation)


def compose(row: tuple[str, str, str], relation: str, object: ObjectReference) -> Tuple:
    """
    Reconstructs a Tuple from one (subject_type, subject_id, subject_relation) row.
    """
    subject_type, subject_id, subject_relation = row
    subject: Subject
    if subject_relation == "":
        subject = DirectSubject(object=ObjectReference(type=subject_type, id=subject_id))
    else:
        subject = SubjectSet(object=ObjectReference(type=subject_type, id=subject_id), relation=subject_relation)

    return Tuple(subject=subject, relation=relation, object=object)
