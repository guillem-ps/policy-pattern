# Architecture

This document defines the shape of the authorization model and evaluator —
everything `docs/semantics.md` deliberately leaves out (that document covers
storage semantics only: mutations, reads, snapshot consistency, and remains
the source of truth for that). This document covers the model, the compile
step, and the evaluator, and how they fit together with the storage port.

## Positioning

`policy-pattern` is not aiming to be the smallest Zanzibar clone. It is a
small, embeddable ReBAC engine for Python designed to make authorization
models understandable, testable, and auditable — that is the filter every
design decision below passes through. Feature breadth that chases
OpenFGA/SpiceDB parity (ABAC, consistency tokens, a text DSL, an HTTP
server) is deliberately out of scope; see "Scope" below.

## ReBAC theory → Python classes

ReBAC (Relationship-Based Access Control) models authorization as a graph
of relationship **facts**, not roles. Zanzibar's canonical notation for one
fact is:

```text
<object>#<relation>@<subject>
```

e.g. `document:42#owner@user:john`. This one line already contains every
concept the model layer needs to represent:

```text
<object>    → ObjectReference(type="document", id="42")
<relation>  → "owner"                     — a name, not an object of its own
<subject>   → DirectSubject(ObjectReference(type="user", id="john"))
```

A **subject can itself be a userset**, not just a person — Zanzibar's other
key idea, needed for groups and nested groups:

```text
group:eng#member@group:backend#member
```

reads as "every member of `group:backend` is also a member of
`group:eng`" — the subject here is `SubjectSet(object=ObjectReference(type="group",
id="backend"), relation="member")`, not a direct entity.

None of `<object>`/`<subject>` carry any meaning about *why* access is
granted by themselves — a tuple is just a stored fact ("this relationship
exists"). What turns a bag of tuples into an authorization **policy** is
the separate question of how relations combine, covered below.

### The graph node: `Identifier` → `ObjectReference`

Every node in the graph (an object being checked, or a subject that is a
concrete entity rather than a userset) is identified the same way: a
`type` and an `id`. `ObjectReference(type: str, id: str)` is that node
type. Both fields are themselves **validated identifiers** — bounded
length, printable, no padding whitespace — which is why `Identifier`
exists underneath it as a reusable validator (see below) rather than each
class inventing its own bounds check.

`ObjectReference` says nothing about relations or permissions — it only
answers "which concrete entity is this," the same role a primary key
plays in a database. It gets reused, not duplicated, everywhere the model
needs to name a concrete entity: as the object of a tuple, and nested
inside `DirectSubject`/`SubjectSet` for the subject side.

### `Relation` vs `Permission`: stored fact vs computed rule

A tuple only says a relationship **exists** — `document:42#parent@folder:eng`
does not by itself imply anyone can view `document:42`. The rule that
turns stored facts into a yes/no answer is the **authorization model**,
split into two distinct kinds of thing (not one namespace shared by both,
unlike OpenFGA):

- **`Relation`** — a storable edge. What `write_tuples()` can actually
  persist. No rewrite logic of its own.
- **`Permission`** — a computed expression over relations/other
  permissions. Never storable; built from `PermissionExpression` (`Reference`,
  `TupleToUserset`, `Union`, `Intersection`, `Exclusion`).

Concretely, the rewrite rules are **set algebra** over "who holds this
relation on this object":

```text
viewer(o) = owner(o) ∪ editor(o)                          Union
can_edit(o) = editor(o) ∩ active_member(o)                Intersection
viewer(o) = member(o) \ blocked(o)                        Exclusion
```

`TupleToUserset` is the one rewrite that isn't a set operation on the
*same* object — it jumps to a *different* object first
(`document:42#parent@folder:eng`) and then evaluates a relation/permission
*there* (`folder:eng#viewer`). This is exactly how a folder hierarchy
grants access to everything under it without copying permissions onto
every child.

### Everything below is one of these two theoretical pieces

Every remaining class in the model is either a **node** (identity, no
meaning by itself — `Identifier`, `ObjectReference`, `Subject`), a **fact**
(`Tuple`, `Mutation`), or **policy** (`Relation`, `Permission`, `Type`,
`Model`). The subsections below give each one's exact Python shape.
**Built** marks what actually exists in `policy_pattern/` today, tested;
everything else is design, not yet implemented.

### `Identifier` (`models/identifier.py`) — Built

`Identifier(value: str, field: str)` — not part of the original design,
introduced during implementation once it became clear almost every
name-shaped string in the model (`ObjectReference.type`/`.id`,
`Relation.allowed_subject_types` entries, and later `Type.name`,
`Reference.name`, `TupleToUserset.tupleset`/`.computed`) needs the exact
same validation: non-empty, bounded length
(`MIN_IDENTIFIER_LENGTH`/`MAX_IDENTIFIER_LENGTH`, currently 1/255),
printable characters only, no leading/trailing whitespace. `field` names
which attribute is being validated, for error context — it is never
externally-sourced, so it only requires non-empty, not the full bounds
check `value` gets.

It is a **validator used by delegation, not a wrapper kept around**: other
Value Objects construct a throwaway `Identifier` per string they need
validated, let `__post_init__` raise on invalid input, and store the
original `str` — never `identifier.value`. This keeps every other class
ergonomic (`reference.type` is a plain `str`, never needs unwrapping)
while centralizing the validation rule in one place.

### `ObjectReference` (`models/object_reference.py`) — Built

`ObjectReference(type: str, id: str)` — a concrete object, e.g.
`document:42`. Delegates both fields to `Identifier` in `__post_init__`.

### `Subject`, `Tuple`, `Mutation` (`models/subject.py`, `models/direct_subject.py`, `models/subject_set.py`, `models/tuple.py`, `models/mutation.py`) — Built

- `Subject` (`models/subject.py`) — `type Subject = DirectSubject |
  SubjectSet` (PEP 695 type alias, not a wrapper class — a wrapper would
  allow the illegal state of both/neither variant set).
- `DirectSubject(object: ObjectReference)` (`models/direct_subject.py`) —
  a concrete subject, e.g. `user:john`; composes `ObjectReference`, does
  not inherit from it.
- `SubjectSet(object: ObjectReference, relation: str)`
  (`models/subject_set.py`) — a userset reference, e.g. `group:eng#member`.
- `Tuple(subject: Subject, relation: str, object: ObjectReference)` — one
  stored fact. `relation` must name a `Relation`, never a `Permission`.
- `Mutation(additions: frozenset[Tuple], deletions: frozenset[Tuple])` — one
  atomic write; `additions`/`deletions` disjoint, empty mutation is a valid
  no-op (`semantics.md`).

All three, like `Identifier`/`ObjectReference`: `@dataclass(frozen=True,
slots=True)`, structural equality and immutability from stdlib, no
external value-object library, no shared `Name` wrapper class — delegate
identifier-shaped fields to `Identifier` the same way `ObjectReference`
does.

### `Relation` (`models/relation.py`) — Built

`Relation(allowed_subject_types: tuple[str, ...])` — a storable edge, no
rewrite algebra. Each entry is a type name (`"user"`) or a userset
restriction (`"organization#member"`) — the same textual shape as
`SubjectSet`, not a separate type; each is delegated to `Identifier`.
`tuple`, not `list`: a `list` field on a `frozen=True` dataclass is still
mutable in place and makes the instance unhashable — the exact gotcha this
project already flagged once for `Mutation`'s `frozenset[Tuple]`. This is
the only thing `TupleStore.write_tuples()` can ever target. Requires at
least one entry — an empty `allowed_subject_types` is a relation nothing
could ever satisfy.

### `PermissionExpression` (`models/operators.py`, `models/reference.py`, `models/tuple_to_userset.py`) — Built

A computed expression, never storable. Base class overloads
`__or__`/`__and__`/`__sub__`; five node types, split across three files by
actual coupling rather than one-file-per-class: `operators.py` holds the
base plus `Union`/`Intersection`/`Exclusion` (they reference the base
class in their own methods, so keeping them together avoids a circular
import); `Reference` and `TupleToUserset` are independent leaves, each in
its own file:

- `Reference(name: str)` — names a relation or permission on the same type;
  the evaluator resolves which one it is at evaluation time.
- `TupleToUserset(tupleset: str, computed: str)` — `tupleset` must resolve
  to a `Relation` (traversal needs stored data, never another computation);
  `computed` is evaluated on the object found via `tupleset`.
- `Union(left, right)`, `Intersection(left, right)`, `Exclusion(include,
  exclude)` (`include - exclude`, binary).

Composition uses real Python operators:

```python
viewer = (
    Reference("owner")
    | (Reference("member") - Reference("blocked"))
    | TupleToUserset(tupleset="parent", computed="viewer")
)
```

This keeps `TupleStore` from ever needing to know about rewrite rules — a
clean port boundary.

### `Type`, `Model`, `CompiledModel` — Built

(`models/type.py`, `models/model.py`, `models/compiled_model.py`)

- `Type(name: str, relations: Mapping[str, Relation], permissions:
  Mapping[str, PermissionExpression])` — one object type's declarations.
  `frozen=True`, but `relations`/`permissions` are wrapped in
  `MappingProxyType` over a copy of the input dict in `__post_init__` — a
  plain `dict` field on a frozen dataclass is still mutable in place and
  unhashable, the same gotcha already noted for `Relation`'s `tuple` vs
  `list` choice above. `name` forbids `#` — one restriction beyond the
  general `Identifier` bound (`docs/semantics.md`): `#` is reserved for
  userset notation (`"type#relation"`) inside `Relation.allowed_subject_types`,
  and a real `Type.name` that could also contain `#` would make that
  notation ambiguous to tell apart from a plain type-name entry.
- `Model(types: dict[str, Type])` — the whole schema, deliberately **not**
  frozen (mutable, authoring-time, built up incrementally), plus
  `.compile() -> CompiledModel`.
- `CompiledModel(types: Mapping[str, Type])` — immutable result of a
  successful `compile()`; the only thing `Evaluator` accepts. Same
  `MappingProxyType`-over-a-copy treatment as `Type`, and the one place it
  matters most: it is `Evaluator`'s trust boundary.

### `TupleStore` / `View` (`ports/tuple_store.py`)

- `TupleStore` — `write_tuples(mutation)`, `delete_tuples(...)`,
  `snapshot() -> View`.
- `View` — `read_tuple(...)` (exact lookup), `read_relation(object,
  relation, limit)` (enumerate, boundable per `semantics.md`).

### `Evaluator` / `EvaluationBudget` (`evaluator.py`)

```python
class Evaluator:
    def __init__(self, model: CompiledModel, store: TupleStore) -> None: ...
    def check(
        self,
        subject: Subject,
        name: str,  # a Relation or Permission name
        object: ObjectReference,
        budget: EvaluationBudget | None = None,  # defaults to EvaluationBudget()
    ) -> bool: ...
```

- `EvaluationBudget(max_depth=25, max_nodes=10_000, max_store_reads=1_000)`
  — passed per call.
- `EvaluationContext` — internal only: `visited`, depth, node/read counters,
  memo.

### Errors (`errors/`) — Built

- `BaseError` — base, `code` `ClassVar`, `message`/`related`
  properties, no `Exception.args` reliance. Shaped after the LSP
  Diagnostic model; see `docs/errors.md` for the full rationale and the
  `PPxxx` code ranges.
- `InvalidIdentifierError` (`PP001`), `InvalidRelationError` (`PP002`),
  `InvalidMutationError` (`PP003`) — construction-time validation errors,
  raised from a Value Object's own `__post_init__`.
- `UnknownTypeError` (`PP004`), `UnknownNameError` (`PP005`) — also
  `PP0xx` by category, but raised from `Evaluator._check_name` against an
  already-compiled model, not from a Value Object's `__post_init__`:
  `UnknownTypeError` when `check()` (or userset expansion) references a
  type the `CompiledModel` never declared; `UnknownNameError` when the
  name is declared as neither a relation nor a permission on its type.
  The actual code-to-class registry lives in `policy_pattern/errors/`
  itself (`grep -r 'code = "PP'`), not duplicated here or in
  `docs/errors.md`.
- `ModelValidationError` (`PP101`, `compile()`-time only) — raised by
  `Model.compile()` for an undeclared `Reference`/`tupleset` name, a
  `tupleset` resolving to a `Permission` instead of a `Relation`, a
  `TupleToUserset.computed` that doesn't resolve to a relation or
  permission on every plain-type target the tupleset relation's
  `allowed_subject_types` allows, or the exhaustiveness fallback for an
  unrecognized expression type.
- `EvaluationError` (`PP201`, runtime: budget exceeded, cycle detected).

No `StorageError` class in v1: `MemoryTupleStore` never raises a storage
error, so there is no consumer for one yet. The contract is "adapters
raise their own errors, always propagated, never swallowed"
(`semantics.md`) — not "inherit from a `policy_pattern` base." Add one
when an adapter that actually raises one exists.

## Module layout

```
policy_pattern/
├── py.typed
├── errors/                      # Built — package, not a single file (see below)
│   ├── base_error.py             # BaseError
│   ├── identifier_error.py       # InvalidIdentifierError (PP001)
│   ├── relation_error.py         # InvalidRelationError (PP002)
│   ├── mutation_error.py         # InvalidMutationError (PP003)
│   ├── unknown_type_error.py     # UnknownTypeError (PP004)
│   ├── unknown_name_error.py     # UnknownNameError (PP005)
│   ├── model_validation_error.py # ModelValidationError (PP101)
│   └── evaluation_error.py       # EvaluationError (PP201)
├── models/
│   ├── identifier.py             # Identifier — Built
│   ├── object_reference.py       # ObjectReference — Built
│   ├── relation.py               # Relation — Built
│   ├── direct_subject.py         # DirectSubject — Built
│   ├── subject_set.py            # SubjectSet — Built
│   ├── subject.py                # Subject (type alias) — Built
│   ├── tuple.py                  # Tuple — Built
│   ├── mutation.py               # Mutation — Built
│   ├── operators.py              # PermissionExpression base, Union, Intersection, Exclusion — Built
│   ├── reference.py              # Reference — Built
│   ├── tuple_to_userset.py       # TupleToUserset — Built
│   ├── type.py                   # Type — Built
│   ├── model.py                  # Model — Built
│   └── compiled_model.py         # CompiledModel — Built
├── ports/
│   └── tuple_store.py            # TupleStore, View — Built
├── adapters/
│   └── memory.py                 # MemoryTupleStore — Built
└── evaluator.py                  # Evaluator, EvaluationBudget — Built
```

`errors/` became a package instead of a single file — each concrete error
plus its own `PPxxx` code gets its own small file, same reasoning as
splitting `models/` by class rather than keeping everything in one
`tuples.py`: one file per concept, split as soon as there's more than one
concept, not before. `postgres.py` under `adapters/` does not exist until
Postgres work actually starts; its dependency will be an optional extra
(`policy-pattern[postgres]`), never a hard dependency.

## Compile step

`Model` (mutable, authoring-time) → `model.compile()` → `CompiledModel`
(immutable). `Evaluator` only ever accepts a `CompiledModel` — evaluating an
unvalidated model is an illegal state, unrepresentable by the type.

`compile()` validates, over the reference graph it builds:

- every `Reference`/`tupleset` name exists on the type
- every `tupleset` resolves to a `Relation`, never a `Permission`

Schema-level cycle detection is not part of `compile()` in v1 — see below
for why that's still safe.

## Cycles are caught at runtime, uniformly

A single guard — `visited`, keyed by `(object, name)`, inside
`EvaluationContext` — catches every cycle, whether it originates from real
data (`folder:A#parent@folder:B` / `folder:B#parent@folder:A` via
`TupleToUserset`, crossing object *instances*) or from a same-object
self-reference with no traversal involved at all. Re-entering an
`(object, name)` pair already being evaluated within one `check()` call
raises `EvaluationError`. There is no separate compile-time schema-cycle
guard: it would only change *when* the error surfaces, never add safety
`visited` doesn't already provide, since neither path can produce a false
allow.

## Evaluator behavior

`check()` opens one `store.snapshot()` `View` internally and evaluates
entirely against it — it never touches `TupleStore` directly, so two
snapshots can never mix inside one `check()` (per `semantics.md`'s
snapshot-consistency requirement).

`EvaluationBudget` tracks more than depth alone: a wide-shallow graph (depth
5, branching 100) can cost more than a deep-narrow one (depth 30, branching
1) — `max_nodes` bounds pure traversal cost, `max_store_reads` bounds actual
I/O cost, and they're tracked independently because a model heavy on
`Union`/`Intersection` combinators and one heavy on `TupleToUserset` spend
their budget very differently.

Evaluation order is deterministic: `Union`/`Intersection` branches are
evaluated left-to-right, in declaration order — never `set`/hash iteration
order. Same model + same tuples + same request + same budget ⇒ same
decision, always.

## Error contract

```
check() -> bool                         the only normal return value
raise EvaluationError                    budget exceeded, cycle detected
raise ModelValidationError               compile()-time only, never at runtime
raise <adapter-specific error>           storage errors always propagate, never swallowed into False
```

No shared `policy_pattern.errors.StorageError` base in v1 — see "ReBAC
theory → Python classes" § Errors above.

`Exclusion` always evaluates both `include` and `exclude` — an error on the
`exclude` side must propagate even if `include` already evaluated to
`False`; swallowing it would manufacture a false allow.

## Ports and adapters

`TupleStore` is a single ABC — not split into separate reader/writer
protocols. No consumer needs that substitutability yet; splitting now would
be an abstraction with one implementation.

`MemoryTupleStore` is the only adapter in v1: lock, copy the tuple set,
release lock, evaluate against the immutable copy (per `semantics.md`'s
Threading section). A future `PostgresTupleStore` does not require touching
`ports/tuple_store.py` or the evaluator.

## Scope

```
v1:    Model (Relation/Permission) + compile() + reference validation
       + Runtime: check(), EvaluationBudget (depth + nodes + reads),
       deterministic evaluation order, uniform runtime cycle guard
v1.x:  compile()-time schema-cycle detection (better error message, not a
       safety requirement), explain() with an explicit trust boundary,
       an invariants API over an explicit fixture set, unused/complexity
       static warnings, Mermaid/DOT visualization
v2:    semantic model diff over an explicit fixture set, text DSL,
       Postgres adapter, OpenFGA/SpiceDB import-export interop
```

`explain()` is deferred specifically because explaining a `DENY` is an
information-disclosure risk (e.g. revealing that `team:backend` exists and
who's in it to a caller who was denied) — it needs an explicit trust
boundary (never wired to the same path as public `check()`) before it's
built. Diff/invariants features must operate only over an explicit,
caller-provided fixture set of checks, never store-wide enumeration, since
`semantics.md` already declares no subject-keyed query / no `ListObjects` as
a v1 non-goal for the storage port.

## Beyond v2 (unscheduled)

Ideas with no target version yet — not committed to any release, listed so
a future proposal for one of these isn't mistaken for a new idea:

- **Reverse lookup** — `ListObjects(subject, relation, object_type)` for
  "which documents can user:7 view?" questions. Different storage access
  pattern from forward `check()`; excluded from the v1 storage port (see
  above).
- **Contextual tuples** — request-scoped relationships that participate in
  one `check()` without being persisted (facts derived from a request,
  token, or application state).
- **Batch checks** — evaluate multiple authorization questions while safely
  reusing evaluation state across them.
- **Model versioning** — explicit versioning and migration of authorization
  models as applications evolve.
- **Advanced consistency** — consistency tokens or another mechanism for
  callers that need a decision tied to a specific, externally-observed
  version of the store.
- **Operational capabilities** — bulk tuple deletion by pattern,
  audit-oriented metadata/history, change notifications.

## Sync, not async

The core (`Evaluator`, `TupleStore`) is synchronous. Evaluation is
CPU/graph-bound from the core's perspective; I/O characteristics belong to
storage adapters and should not dictate the core API shape. If a future
`PostgresTupleStore` wants async I/O, that is an adapter-level concern (or a
parallel package), not a reason to make `MemoryTupleStore` — which has no
I/O — pay for `await` everywhere.
