"""
Type alias for a subject in the authorization graph.

A subject is either a `DirectSubject` (a reference to one concrete entity,
e.g. `user:john`) or a `SubjectSet` (a reference to a relation on an
object — a computed set of subjects, e.g. `group:eng#member`). Deliberately
a type alias, not a wrapper class: `DirectSubject`/`SubjectSet` are already
distinguishable by `isinstance`, and a wrapper with two `Optional` fields
would allow two illegal states a real union can't represent — neither set,
or both set at once. Anywhere a `Subject` is expected, construct one of the
two variants directly (`DirectSubject(...)` / `SubjectSet(...)`) and narrow
with `isinstance`/`match` where it matters, e.g. inside the evaluator.

Example:
    subject: Subject = DirectSubject(object=ObjectReference(type="user", id="john"))
    subject: Subject = SubjectSet(object=ObjectReference(type="group", id="eng"), relation="member")
"""

from .direct_subject import DirectSubject
from .subject_set import SubjectSet

type Subject = DirectSubject | SubjectSet
