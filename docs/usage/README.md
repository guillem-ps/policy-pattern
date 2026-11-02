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

`check_many()` answers the same question for many requests at once, when the caller already has a list of
candidates to filter:

```python
candidates = [document_42, ObjectReference(type="document", id="7"), ObjectReference(type="document", id="99")]
decisions = evaluator.check_many([(alice, "viewer", document) for document in candidates])
# [True, False, False] — only document:42 has a tuple granting alice access

allowed = [document for document, decision in zip(candidates, decisions, strict=True) if decision]
```

The whole batch runs inside one `store.snapshot()` and shares one evaluation cache, so a sub-check several
requests depend on — a parent folder's `viewer`, say — is computed once rather than once per request. The
returned list is aligned to `requests` by position, duplicates included.

This filters a candidate set; it does not discover one — the caller supplies the candidates, usually
straight from its own business data. The budget is shared across the batch too, so a batch large enough
to exhaust it raises `EvaluationError` rather than returning a short list. For the reverse question
("which documents can alice view?"), see [`list_objects()`](#list_objects--reverse-lookup) below.

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

## `list_objects()` — reverse lookup

`check()` and `check_many()` answer "does this subject hold this permission on this object" — the
caller already names the object(s). `list_objects()` answers the reverse question: "which objects of
this type does this subject hold this permission on", with no candidate set supplied. It walks the
store backward from `subject` (following direct grants, group membership, and the same `parent`-style
links `TupleToUserset` follows forward) to find candidates, then filters every candidate through the
same `check()` path — so it can never return an object `check()` would deny. Using the facts built up
over this guide — bob is a member of `group:eng`, which is `editor` on `document:42`; carol has
`viewer` on `folder:engineering`, which is `document:99`'s `parent`:

```python
evaluator.list_objects(bob, "inherited_viewer", "document")  # {document_42}   — via group:eng#member
evaluator.list_objects(alice, "inherited_viewer", "document")  # {document_42}   — direct owner
evaluator.list_objects(carol, "inherited_viewer", "document")  # {document_99}   — via folder:engineering
```

If the caller already has its own candidate set — the common case when objects come from a paginated
business query — pass it as `candidate_ids` to skip the reverse walk entirely and go straight to the
`check()` filter:

```python
candidates = frozenset({document_42, document_99, ObjectReference(type="document", id="7")})
evaluator.list_objects(bob, "inherited_viewer", "document", candidate_ids=candidates)  # {document_42}
```

`document_99` and `document:7` are excluded by the same `check()` filter `candidate_ids` always goes through — `candidate_ids` only narrows the search, it never grants anything `check()` wouldn't (unlike `check_many()`, which returns a decision per request and leaves the filtering to the caller, `list_objects()` does that filtering itself). 

The reverse walk shares `EvaluationBudget` with the forward filter (one budget for the whole call, same rule as `check_many()`), so a subject reachable through an unusually large fan-out raises `EvaluationError` rather than silently returning a partial result.

## `EvaluationBudget`

Every `check()` call is bounded — `EvaluationBudget` caps how much work one call can do, defaulting to
`max_depth=25`, `max_nodes=10_000`, `max_store_reads=1_000`:

```python
from policy_pattern.evaluator import EvaluationBudget

evaluator.check(alice, "viewer", document_42, budget=EvaluationBudget(max_depth=5, max_nodes=100, max_store_reads=50))
```

A `check()` that would need more than the budget allows raises `EvaluationError` — it never silently returns `False` because it ran out of budget. A cycle in the stored data (however it got there) raises the same error, for the same reason: an ambiguous or unbounded evaluation is not a safe "no."

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

`PostgresTupleStore` stores tuples in a PostgreSQL table. By default, it does not create or migrate that schema: the host service applies the change through its migration tool (Alembic, a raw-SQL migration step, etc.).

As an opt-in convenience, pass `auto_create_schema=True` to create the table from the packaged migration when constructing the adapter. This requires the connection role to have `CREATE` privilege. It runs `CREATE TABLE IF NOT EXISTS`; it does not track migration history or verify an existing table's schema, so use your service's migration workflow when you need managed schema changes.

The matching DDL ships as two package resources, applied in order, not as
code the library runs:

```python
from importlib.resources import files

for resource in (
    "0001_create_policy_tuples.sql",  # the table itself
    "0002_add_subject_index.sql",  # the index list_objects() needs
):
    migration_sql = files("policy_pattern").joinpath("sql", "postgres", resource).read_text()
    ...  # hand each to your migration tool, same order
```

Hand each string to your migration tool the same way you'd hand it any other raw-SQL migration step — e.g. `op.execute(migration_sql)` per revision in Alembic. For the default setup, apply both once before the service that uses `PostgresTupleStore` starts. With
`auto_create_schema=True`, the adapter runs both packaged statements at construction instead, each in its own transaction.

**On an existing deployment with a populated table**, `0002`'s `CREATE INDEX` (without `CONCURRENTLY`) holds a lock that blocks writes to `authz_tuples` for as long as the index build takes. `auto_create_schema` cannot use `CREATE INDEX CONCURRENTLY` itself — this adapter requires `autocommit=False` on every connection (documented below), and `CONCURRENTLY` cannot run inside any transaction, not even an implicit one-statement one. If the table already has real data, apply this index manually with `CREATE INDEX CONCURRENTLY authz_tuples_subject_idx ON "authz_tuples" (subject_type, subject_id, subject_relation);` outside `auto_create_schema`, ahead of upgrading, instead of letting the packaged migration take the lock.

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

- **With the default setting, runtime credentials need only
  `SELECT`/`INSERT`/`DELETE` on the tuple table.** If you enable `auto_create_schema`, the connection role also needs `CREATE` privilege.
- **A missing table is not handled specially.** If the migration was
  never applied, the first query raises the driver's own "relation does not exist" error when using the default setting. With `auto_create_schema=True`, the adapter attempts to create the table during construction.
- **Writing a tuple is not in the same transaction as your own business
  writes.** `write_tuples()` commits its own transaction when it returns. If a request needs "update this business row and record this permission tuple atomically," that's a  cross-transaction coordination problem your service has to solve itself — `policy-pattern` does not provide a way to enlist both in one transaction.
- **An `Identifier` valid by its own rules can still be too large for
  this adapter.** `Identifier` bounds a value by code points (255 max, any printable Unicode), not encoded bytes. `write_tuples()` checks the encoded size of an addition's primary key before acquiring a connection and raises `IndexEntryTooLargeError` (`PP900`) if it would exceed PostgreSQL's B-tree index entry limit, instead of letting the driver's own cryptic "index row size exceeds btree ... maximum" error surface.