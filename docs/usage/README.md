# 🧱 Usage Guide

This guide walks through `policy-pattern` end to end: defining an authorization model, compiling it, writing facts,
and evaluating `check()` against every rewrite operator. Every snippet below is real, runnable code — not
pseudocode — verified against the actual API, and they all build on the *same* model and store, top to bottom.

## Core Models

An authorization schema is a `Model`: a mutable, authoring-time collection of `Type` declarations. Each `Type` names
its **relations** (storable facts) and **permissions** (computed rewrite rules). A `Type`'s `relations`/`permissions`
are frozen once constructed — extending a schema means declaring a new `Type`, not mutating an existing one — so the
whole model this guide uses is declared once, upfront:

```python
from policy_pattern.models import (
    Model,
    Type,
    Relation,
    Reference,
    Union,
    Intersection,
    Exclusion,
    TupleToUserset,
)

model = Model()
model.types["document"] = Type(
    name="document",
    relations={
        "owner": Relation(allowed_subject_types=("user",)),
        "editor": Relation(allowed_subject_types=("user", "group#member")),
        "blocked": Relation(allowed_subject_types=("user",)),
        "parent": Relation(allowed_subject_types=("folder",)),
    },
    permissions={
        "viewer": Union(left=Reference(name="owner"), right=Reference(name="editor")),
        "manager": Intersection(left=Reference(name="owner"), right=Reference(name="editor")),
        "restricted_viewer": Exclusion(include=Reference(name="owner"), exclude=Reference(name="blocked")),
        "inherited_viewer": Union(
            left=Reference(name="viewer"),
            right=TupleToUserset(tupleset="parent", computed="viewer"),
        ),
    },
)
model.types["folder"] = Type(
    name="folder",
    relations={"viewer": Relation(allowed_subject_types=("user",))},
    permissions={},
)
model.types["group"] = Type(
    name="group",
    relations={"member": Relation(allowed_subject_types=("user", "group#member"))},
    permissions={},
)
```

`allowed_subject_types` lists what a relation's stored subject can be — a plain type name (`"user"`) or a userset
restriction (`"group#member"`, meaning "members of a group"). A `Relation` never carries rewrite logic of its own;
that is what `permissions` are for. `manager`, `restricted_viewer` and `inherited_viewer` use operators explained
below in [Rewrite Operators](#rewrite-operators) and [`TupleToUserset`](#tupletouserset--traversing-to-a-related-object)
— they're declared now so every section of this guide checks against one compiled model.

Once every type is declared, `compile()` validates the whole model and returns an immutable `CompiledModel` — the
only thing an `Evaluator` accepts:

```python
compiled = model.compile()
```

`compile()` checks that every `Reference`/`tupleset` name actually exists on its type, and that a `tupleset` always
resolves to a `Relation`, never a `Permission`. An invalid model raises `ModelValidationError`, never a silent
success:

```python
from policy_pattern.errors import ModelValidationError

try:
    Model(
        types={"document": Type(name="document", relations={}, permissions={"viewer": Reference(name="missing")})}
    ).compile()
except ModelValidationError as error:
    print(error.message)  # "document.viewer references undeclared name 'missing'"
```

## Writing Facts

Facts live in a `TupleStore` — `MemoryTupleStore` is the one shipped in v1. A fact is a `Tuple`:
`(subject, relation, object)`. `subject` is either a `DirectSubject` (a concrete entity) or a `SubjectSet` (a
userset, e.g. "every member of this group"):

```python
from policy_pattern.adapters.memory import MemoryTupleStore
from policy_pattern.models import DirectSubject, Mutation, ObjectReference, Tuple

store = MemoryTupleStore()
alice = DirectSubject(object=ObjectReference(type="user", id="alice"))
document_42 = ObjectReference(type="document", id="42")

store.write_tuples(
    Mutation(
        additions=frozenset({Tuple(subject=alice, relation="owner", object=document_42)}),
        deletions=frozenset(),
    )
)
```

A `Mutation` is always atomic — `additions` and `deletions` apply together or not at all, and the two sets must be
disjoint (a tuple can't be added and deleted by the same `Mutation`). An empty `Mutation` is a valid no-op.

## Evaluating

`Evaluator` binds one `CompiledModel` to one `TupleStore`. `check()` answers whether a subject holds a relation or
permission on an object:

```python
from policy_pattern.evaluator import Evaluator

evaluator = Evaluator(model=compiled, store=store)
evaluator.check(alice, "viewer", document_42)  # True — alice is a direct owner
```

## Rewrite Operators

Permissions compose with real Python operators:

| Python expression | Node | Meaning |
| --- | --- | --- |
| `left | right` | `Union` | Either side holds |
| `left & right` | `Intersection` | Both sides hold |
| `include - exclude` | `Exclusion` | `include` holds and `exclude` does not |

```python
viewer = Reference(name="owner") | Reference(name="editor")
manager = Reference(name="owner") & Reference(name="editor")
restricted_viewer = Reference(name="owner") - Reference(name="blocked")
```

`Union`/`Intersection` are evaluated left-to-right and may short-circuit — if the left side already decides the
result, the right side is never evaluated. `Exclusion` **never** short-circuits: both `include` and `exclude` are
always evaluated, because skipping `exclude` could silently manufacture a false allow.

## Nested groups

A relation's stored subject can itself be a `SubjectSet` — `policy-pattern` follows it automatically, however deep
the nesting:

```python
from policy_pattern.models import SubjectSet

engineering = ObjectReference(type="group", id="eng")
bob = DirectSubject(object=ObjectReference(type="user", id="bob"))

store.write_tuples(
    Mutation(
        additions=frozenset(
            {
                # document:42#editor@group:eng#member — every member of group:eng is an editor
                Tuple(subject=SubjectSet(object=engineering, relation="member"), relation="editor", object=document_42),
                # bob is a direct member of group:eng
                Tuple(subject=bob, relation="member", object=engineering),
            }
        ),
        deletions=frozenset(),
    )
)

evaluator.check(bob, "viewer", document_42)  # True — via editor, via group membership
```

## `TupleToUserset` — traversing to a related object

Some permissions depend on a *different* object's permission — the canonical case is folder hierarchies. `document`
already declared a `parent` relation and an `inherited_viewer` permission above; only the `folder` facts are new:

```python
folder_eng = ObjectReference(type="folder", id="engineering")
document_99 = ObjectReference(type="document", id="99")
carol = DirectSubject(object=ObjectReference(type="user", id="carol"))

store.write_tuples(
    Mutation(
        additions=frozenset(
            {
                Tuple(subject=DirectSubject(object=folder_eng), relation="parent", object=document_99),
                Tuple(subject=carol, relation="viewer", object=folder_eng),
            }
        ),
        deletions=frozenset(),
    )
)

evaluator.check(carol, "inherited_viewer", document_99)  # True — via folder:engineering's viewer
```

`TupleToUserset(tupleset="parent", computed="viewer")` reads: "find the object(s) related to this one via `parent`,
then check `viewer` on *that* object instead." This is how a document under `folder:engineering` inherits access
from the folder without copying a permission onto every document individually.

## `EvaluationBudget`

Every `check()` call is bounded — `EvaluationBudget` caps how much work one call can do, defaulting to
`max_depth=25`, `max_nodes=10_000`, `max_store_reads=1_000`:

```python
from policy_pattern.evaluator import EvaluationBudget

evaluator.check(alice, "viewer", document_42, budget=EvaluationBudget(max_depth=5, max_nodes=100, max_store_reads=50))
```

A `check()` that would need more than the budget allows raises `EvaluationError` — it never silently returns
`False` because it ran out of budget. A cycle in the stored data (however it got there) raises the same error, for
the same reason: an ambiguous or unbounded evaluation is not a safe "no."

## Error Handling

| Exception | Code | Raised when |
| --- | --- | --- |
| `ModelValidationError` | `PP101` | `compile()` finds an undeclared reference or a `tupleset` that isn't a relation |
| `EvaluationError` | `PP201` | A cycle was detected, or an `EvaluationBudget` limit was exceeded |
| `UnknownTypeError` | `PP202` | `check()` (or userset expansion) references a type not declared in the `CompiledModel` |
| `UnknownNameError` | `PP203` | `check()` references a name declared as neither a relation nor a permission |

```python
from policy_pattern.errors import UnknownTypeError

try:
    evaluator.check(alice, "owner", ObjectReference(type="not_a_real_type", id="1"))
except UnknownTypeError as error:
    print(error.message)  # "type 'not_a_real_type' is not declared in this CompiledModel"
```

See [Errors](../errors.md) for the full code registry and design rationale.

## Using `PostgresTupleStore`

`PostgresTupleStore` stores tuples in a PostgreSQL table. It never creates
or migrates that schema itself — schema changes are the host service's
own responsibility, applied through whatever migration tool it already
uses (Alembic, a raw-SQL migration step, etc.).

The matching DDL ships as a package resource, not as code the library
runs:

```python
from importlib.resources import files

migration_sql = files("policy_pattern").joinpath("sql", "postgres", "0001_create_policy_tuples.sql").read_text()
```

Hand that string to your migration tool the same way you'd hand it any
other raw-SQL migration step — e.g. `op.execute(migration_sql)` in an
Alembic revision. Apply it once, before the service that uses
`PostgresTupleStore` ever starts.

Once the schema exists, construct the adapter with a real connection pool:

```python
from psycopg_pool import ConnectionPool
from policy_pattern.adapters.postgres import PostgresTupleStore
from policy_pattern.models import DirectSubject, Mutation, ObjectReference, Tuple

pool = ConnectionPool("postgresql://...")  # opened/closed by your app
store = PostgresTupleStore(pool)

alice = DirectSubject(object=ObjectReference(type="user", id="alice"))
document_42 = ObjectReference(type="document", id="42")
t = Tuple(subject=alice, relation="viewer", object=document_42)

store.write_tuples(Mutation(additions=frozenset({t}), deletions=frozenset()))
with store.snapshot() as view:
    view.read_tuple(alice, "viewer", document_42)
```

Three things worth knowing before relying on this in a real service:

- **Runtime credentials need only `SELECT`/`INSERT`/`DELETE` on the tuple
  table.** `CREATE TABLE` privileges belong to whatever role runs your
  migrations, not to the role `PostgresTupleStore` connects with day to
  day — the adapter never issues a schema-changing statement.
- **A missing table is not handled specially.** If the migration was
  never applied, the first query raises the driver's own "relation does
  not exist" error. `PostgresTupleStore` does not check for the table's
  existence, and does not create it on your behalf, by design.
- **Writing a tuple is not in the same transaction as your own business
  writes.** `write_tuples()` commits its own transaction when it
  returns. If a request needs "update this business row and record this
  permission tuple atomically," that's a cross-transaction coordination
  problem your service has to solve itself — `policy-pattern` does not
  provide a way to enlist both in one transaction.
