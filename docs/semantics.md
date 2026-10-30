# Semantics

This document defines the observable behavior `policy-pattern` guarantees, independent of any particular storage adapter. It is the source of truth for what "correct" means in this library — more important than any single adapter's Python interface. Every adapter (`MemoryTupleStore`,
`PostgresTupleStore`, and any future one) must satisfy the contract below, verified by a shared contract test suite that runs against all of them.

This document covers **storage semantics** only — mutations, reads, and consistency. Evaluation semantics (union, intersection, exclusion,
tuple-to-userset, recursion, cycle handling) and public API semantics (`check()`'s exact error contract) live in `docs/architecture.md` instead —
deliberately not duplicated here.

A note on scope: this document states *what must be true*. It deliberately avoids naming how a specific adapter achieves it (e.g. which PostgreSQL isolation level or index it uses) — that belongs in that adapter's own design notes, not in the cross-adapter contract.

## Authorization store / namespace

An authorization store (namespace) is the isolation boundary within which tuples, mutations, and snapshots are scoped. `policy-pattern` assigns it no further meaning. Applications may use a store per tenant, per environment, or any other scheme that fits their needs — that is an application-level decision, not something this library encodes.

**Cross-store mutations are not representable, by construction.** A `TupleStore` instance (or handle) is bound to exactly one authorization
store. Mutation and read calls do not take a store identifier as a parameter — there is no field to put a second store's id into. This is
stronger than "reject cross-store input at runtime": the shape of the API makes the invalid case impossible to express in the first place.

## Valid tuple domain

### Schema-agnostic storage

-`TupleStore` stores and compares structurally well-formed
-`(subject, relation, object)` triples. It does **not** validate that a
-`relation` or type is declared in an `AuthorizationModel`, or that an
-`object`'s type accepts that relation. That validation belongs to a layer above storage (the model/validation layer), not to `TupleStore` — a
- `PostgresTupleStore` that starts rejecting unknown relations while
- `MemoryTupleStore` accepts them silently breaks substitutability between
adapters, which the contract tests exist to catch.

### Identifier bounds

Identifiers are not unbounded free text. For a library sitting on the
authorization path, an unbounded identifier is a DoS and correctness
surface, not just a style question. Every adapter enforces the same bounds,
so no adapter is more permissive than another:

- non-empty,
- a bounded maximum length (an exact shared constant, not "whatever the
  database column allows"),
- restricted to a safe character set that excludes control characters,
- no leading or trailing whitespace (accidental padding, not meaningful
  content — a caller who genuinely needs a boundary space is almost
  certainly passing in a copy-paste artifact, not an intentional id).

The exact numeric bound is an implementation constant `policy-pattern`
defines once and every adapter enforces identically — not something each
adapter chooses independently.

### Identifier content vs. canonical serialization

**Identifier *content* is not restricted to exclude `:`, `#`, or `@`.**
A real-world `id` — an email address (`john@example.com`), a UUID, a
path — may legitimately contain any of these characters, and requiring
callers to pre-encode such values before they can name a `user` would be
the library imposing friction that its own structural-equality design was
supposed to avoid.

The **structured** form (`Object(type="user", id="john@example.com")`)
is authoritative and has no ambiguity — it is Python objects, not a string
to scan. Ambiguity only appears in the **canonical textual serialization**
(`user:john@example.com` / `document:42#owner@user:john`), where
`:`, `#`, and `@` are structural separators and therefore need an escaping
or encoding rule when they also appear inside a component's content.

```text
Identifier semantics (this section):
    id/type/relation content — effectively unrestricted, bounded only by
    length, control-character exclusion, and no leading/trailing
    whitespace, above.

Canonical textual serialization (separate, not yet specified):
    a grammar + escaping scheme that can round-trip any valid identifier
    through the "type:id" / "type:id#relation" text form without
    ambiguity. `PostgresTupleStore` sidesteps the need entirely — it stores
    each component in its own structured column
    (`object_type`/`object_id`/`relation`/`subject_type`/`subject_id`/
    `subject_relation`), never a single serialized text key. Still needed
    the moment a consumer actually wants one text key (logs, a wire format,
    a different adapter's storage shape) — not yet designed, not silently
    absent, tracked as a follow-up once that need is real.
```

Equality and comparison always operate on the **structured** form (see
"Identity and equality" below) — never on the serialized string — which is
exactly what makes deferring the serialization grammar safe to do without
blocking implementation of the structured API itself.

## Write mutations

### Duplicate tuples

Duplicate tuples do not exist as a concept. A store is a **set** of
`(subject, relation, object)` triples, not a multiset. Writing a tuple that
already exists changes nothing.

### Write idempotency

Writing an existing tuple again is a no-op: the resulting state is identical
to writing it once.

### A mutation is `(additions, deletions)`

A single mutation applies a set of additions `A` and a set of deletions `D`
to state `S`, producing:

```text
S' = (S - D) ∪ A
```

**`A` and `D` must be disjoint.** Since tuples within a mutation are
unordered (see below), a mutation that both adds and deletes the same tuple
has no well-defined meaning — there is no "it depends on order" answer to
fall back on, because order was never a thing to begin with. An adapter
that receives such a mutation must reject the entire mutation as invalid
(`InvalidMutationSet` or equivalent) and apply nothing, rather than guess.

**An empty mutation (`A = ∅, D = ∅`) is a valid no-op**, consistent with
the idempotency reasoning throughout this document — not a special case
to reject.

**Validation applies to the mutation as a whole, not tuple-by-tuple.** If
any single tuple in the batch fails validation (identifier bounds,
structural well-formedness), the entire mutation is rejected and nothing
in it becomes visible — never "apply the 99 valid tuples, skip the one bad
one." This follows from atomicity, but is worth stating on its own: it is
cheap to verify directly as two contract tests (empty mutation succeeds as
a no-op; one invalid tuple among many valid ones rejects the whole batch).

### Ordering

Ordering between distinct tuples in the same mutation is neither guaranteed
nor meaningful. A mutation is a set of additions and a set of deletions, not
a sequence.

### Atomicity

A mutation **must** be atomic: it becomes visible as a whole, or not at all.
This is a requirement, not an optimization — "transfer ownership" is really
"delete old tuple + add new tuple" as one logical step, and without
atomicity there is a window where either zero or two owners exist.

Atomicity is a statement about **visibility**, not just about one writer not
interrupting another writer. No observer — including a concurrent
`check()` — may see a partial mutation. An adapter that locks writers
against each other but lets a reader observe state mid-mutation does not
satisfy this contract.

Atomicity does **not** imply any cardinality or business invariant, such as
"an object has exactly one owner". A relation may legitimately have
multiple subjects (`document:42#owner@user:a` and
`document:42#owner@user:b` can coexist) — that is a normal ReBAC shape, not
a bug. Two concurrent mutations that each replace `owner` with a different
subject are two independent, individually-atomic mutations; nothing here
serializes them against each other or enforces single-ownership. If an
application needs that guarantee, it is a business invariant enforced above
this layer, not a `TupleStore` property.

### Deleting a nonexistent tuple

Deleting a tuple that does not exist is a no-op that succeeds. This follows
the same reasoning as write idempotency: the caller's desired end state (the
tuple is absent) already holds, so there is no need to check existence
first, which would only introduce a TOCTOU race. An adapter may return an
affected-row count for optional debugging.

**This does not override storage error propagation.** *Absence of the
tuple* is not an error and must not itself cause an exception — but if the
adapter cannot even determine whether the tuple was absent (storage
unreachable, validation failure), that failure still propagates normally,
per "storage errors are not empty results" below. "Never raise" applies to
the not-found case specifically, not to every possible failure of a delete
call.

### Visibility point

Define one term and use it everywhere instead of transaction language:
**visibility point** — the logical instant at which a successful mutation's
effects become observable, according to whatever consistency mechanism the
adapter uses internally. The precise requirement: **every successful
mutation has exactly one visibility point.** (Deliberately not "total" —
that word could be misread as a total ordering across mutations, which is
not guaranteed and would contradict the undefined write/delete race outcome
below. This contract cares only that a visibility point exists, not that
visibility points across different mutations are comparable or ordered.)

> **Non-normative implementation note:** `PostgresTupleStore` is expected
> to implement a visibility point as a transaction commit;
> `MemoryTupleStore` has no transactions and is expected to implement it as
> the instant a lock is released after an in-place update. Neither example
> is part of the contract — only "a visibility point exists" is.

### Write visibility

**A successful mutation call must not return before its visibility point
has been reached.** This rules out queue-then-apply-asynchronously
implementations by construction: v1 is read-after-write, not eventually
consistent, and a `write_tuples()` that returns success while the effect
is still "on its way to becoming visible" would technically satisfy every
sentence above while violating what those sentences are actually for.

```text
mutation applied → visibility point → return success → later snapshots see it

NEVER:
return success → visibility point reached sometime after
```

If a mutation reaches its visibility point, any `check()` (or read) whose
snapshot is established afterward must observe its effects — **unless those
effects have since been superseded by another mutation that has itself
reached its visibility point.** A write followed by a concurrent delete of
the same tuple does not obligate a later `check()` to see the
(now-superseded) write; it must see current state.

### Concurrent writes

Concurrent writes of the *same* tuple have no lost-update problem: the union
of concurrent additions is well-defined regardless of interleaving.

Deliberately left unspecified: a race between a write and a delete of the
same tuple. The winner is undefined; a caller that needs a specific outcome
must sequence its own calls, not rely on timing.

## Reads

### Query capabilities

The port exposes only the read shapes forward `check()` evaluation actually
needs:

- **exact tuple lookup**: does `(subject, relation, object)` exist?
- **enumerate by `(object, relation)`**: which subjects/usersets hold this
  relation on this object? Needed for direct relations and as the base case
  for union, intersection, exclusion, and tuple-to-userset traversal.

There is deliberately **no subject-keyed query** ("find all tuples for this
subject") in v1. Forward evaluation never needs it — it always starts from
the queried object and walks relations outward, never the reverse. A
subject-keyed query is what reverse lookup / `ListObjects` ("which documents
can John view?") needs, and that is explicitly out of scope for v1. Don't
add it just because it looks symmetric with `(object, relation)` lookup;
add it only when `ListObjects` is actually being designed.

Whatever concrete Python method names implement these two shapes is an
interface detail, not part of this contract — only the two capabilities
above are normative for v1.

### Enumeration must be boundable

"No pagination" (see non-goals below) is a statement about the *public
API shape* — no cursor, no resume token. It is **not** a statement that
`enumerate(object, relation)` may materialize an unbounded number of
tuples before anything can stop it.

This matters because of *when* an evaluator's own work-budget check can
run relative to storage work. Consider tuple-to-userset traversal over
`folder:root#parent`, if five million folders all declared `root` as
their parent: fully enumerating that relation — DB round-trip, network,
deserialization, Python object allocation — happens *before* the
evaluator gets a chance to say "budget exceeded," if enumeration has no
way to stop early. A bounded-work check that only fires after the
unbounded read already completed is not a mitigation.

The capability required:

```text
Enumeration MUST be boundable by the caller's remaining evaluation
budget. The concrete mechanism is not part of this contract.
```

Conceptually (not a final API):

```python
view.read_relation(object, relation, limit=remaining_budget + 1)
```

This is orthogonal to pagination: pagination lets a caller walk through
*all* results across multiple calls; a bound lets a caller cap how much a
*single* call is allowed to produce. v1 needs the second, explicitly does
not need the first.

### A truncated result must never look like a complete one

Bounding enumeration introduces a new failure mode if left unspecified:
with a bound of 100 tuples, "here are the 100 matching tuples, that's all
of them" and "here are the first 100 of 1,000 matching tuples" must not be
representable as the same return value. This is not a performance nitpick
— it's correctness. The subject that would flip a `check()` to `ALLOW`
(or, on the other side of an exclusion, to `DENY`) could be the 101st
match. Silently truncating and calling it complete manufactures a wrong
answer exactly the same way an empty-on-error shortcut does:

```text
storage failure  ≠ empty result      (established above)
truncated result ≠ complete result   (this section)
```

The required invariant:

```text
A bounded enumeration MUST NOT silently present a truncated result as
complete. If more matching tuples exist than the bound allows, the
caller MUST be able to distinguish that from "no more tuples exist."
```

The mechanism is not fixed by this contract — an explicit
`complete: bool` flag on the result, a distinct exception, or requesting
`limit + 1` and treating a full `limit + 1` response as "budget exceeded"
are all conforming options. Once evaluation semantics are designed, they
must not be able to collapse "budget exhausted" into "relation has no
further members" — that distinction has to survive all the way up through
union, intersection, exclusion, and tuple-to-userset.

### `read_relation(...)` result shape

Returns a **set** (a `frozenset`, per `ReadResult.tuples`) — never
duplicates. Ordering is unspecified. Filtering is exact match on the
requested fields; no partial or fuzzy matching.

Subject usersets (e.g. `group:eng#member` as a subject) are returned exactly
as stored — `read_relation` does not resolve or expand them. Resolution is
the evaluator's job, not storage's.

A single logical `read_relation()` call must reflect **one** consistent store
state, even if an adapter implements it internally via multiple statements
or pages. If a read can't be answered from one consistent state, it must
fail rather than silently blend two states — the same principle as
snapshot consistency of `check()` below, applied to a standalone read.

### Storage errors are not empty results

**A storage error must raise, never be swallowed into an empty set.** This
is the single most important line in this document.

```text
except StorageError:
    return set()   # NEVER DO THIS
```

Consider `viewer = member - blocked`. If the read for `blocked` fails and
that failure is silently treated as "no blocked tuples", the exclusion
computes `member - ∅`, i.e. everyone in `member` is granted — a false allow
manufactured entirely out of a storage failure. `[] → relation absent → deny`
is a tempting shortcut for unions, but it is actively dangerous the moment
exclusion is involved. Failure to read must always be distinguishable from
"nothing found", and must propagate as an error, never as a default deny
*or* default allow computed from an incomplete read.

## Snapshot consistency of `check()`

**Every `check()` evaluates against exactly one logically consistent
snapshot of the authorization store.** A `check()` must never combine tuple
states read from different versions of the store, even when it internally
issues multiple reads.

This matters concretely for exclusion. Take `viewer = member - blocked`,
with `member(user:x) = true` and `blocked(user:x) = true` (net: deny). A
concurrent mutation atomically deletes both tuples (net result: still deny).
If `check()`'s two reads are not pinned to one snapshot, it can legally
observe `member → true` (read before the concurrent mutation's visibility
point) and `blocked → false` (read after it) — a composite state that never
existed in the store at any point in time, yielding `true - false = allow`.
That is a false allow constructed purely from evaluation-time snapshot
drift, not from any bug in the mutation itself.

Concurrent mutations may complete while a `check()` is in flight; the
`check()` must evaluate entirely against either the snapshot in effect when
it started or an equivalently consistent later one — never a mix of the two.
An adapter backed by a database whose default read isolation takes a new
snapshot per statement (rather than per logical operation) does not satisfy
this by default and must explicitly opt into a stronger guarantee for the
lifetime of a `check()`.

### The port must expose an evaluation-scoped view

Snapshot consistency across *multiple reads* cannot be a property `check()`
gets for free — each individual `read_relation()` call being internally
consistent (see above) says nothing about two separate calls agreeing with
each other. If the evaluator makes ten reads while resolving one `check()`,
the port needs a way to say "these ten belong to the same view." Naming a
requirement without giving the port a way to satisfy it is itself a gap.

The port must therefore expose an **evaluation-scoped read view**: a handle
that pins one snapshot for the lifetime of one `check()`, through which all
of that check's reads are issued.

```text
TupleStore must provide an evaluation-scoped read view.

All reads performed through the same view observe the same logical
store state, regardless of how many individual reads are issued.
```

**An evaluation-scoped view is read-only.** Mutations are issued against
the `TupleStore` itself, never through a view. This keeps the boundary
clean —

```text
TupleStore
├── mutations
└── open a view
        └── reads only
```

— and sidesteps a question v1 doesn't need to answer: whether a write
issued through a snapshot would be visible within that same snapshot. It
can't come up if a view has no write operation at all.

Conceptually (not a final Python API — the capability is normative, the
method names are not):

```python
with store.snapshot() as view:
    evaluator.check(subject, relation, object, view=view)
```

> **Non-normative implementation note:** `PostgresTupleStore` is expected to
> implement this as a single `REPEATABLE READ` transaction held open for
> the view's lifetime. `MemoryTupleStore` cannot satisfy it by re-acquiring
> a lock per read — the lock could be released and reacquired between two
> reads, letting a mutation land in between, which reproduces exactly the
> same drift bug as an ungrouped multi-statement Postgres transaction. See
> the `MemoryTupleStore` section below for that adapter's expected
> strategy. Neither strategy is part of the contract — only "one view, one
> consistent snapshot, for however many reads it serves" is.

```text
check A ─────────── snapshot V1 ───────────> result
check B                    ─── snapshot V2 ──> result

NEVER:
check C   reads half from V1, half from V2 → synthetic state "V1.5"
```

## Identity and equality

Tuple equality is **structural**, evaluated after parsing into
`(subject, relation, object)` components — not by comparing serialized
strings. `policy-pattern` performs **no normalization** of identifier
values (no case-folding, no Unicode normalization, no numeric coercion).
Two tuples are equal iff their parsed subject, relation, and object
components are exactly equal.

Identifiers are therefore case-sensitive and compared by **exact
string/code-point equality** — not byte-exact. The Python API deals in
`str` (Unicode code point sequences), not encoded bytes, so there is no
encoding to be exact about. What "no normalization" actually guarantees:
`"é"` (U+00E9, precomposed) and `"e" + "́"` (U+0065 + combining acute
accent, decomposed) are **not equal**, because they are different code
point sequences and this library performs no Unicode normalization to
reconcile them — even though both render identically and a human reading
either string would call them "the same." They typically originate from
external systems (UUIDs, emails) where silently folding case or Unicode
form could collide two distinct entities. Normalizing identifiers before
calling into `policy-pattern` (e.g. always storing emails lowercased,
NFC-normalized) is the caller's responsibility — this library does not
guess at what normalization would be safe for a given identifier space.

A `subject` may itself be a userset reference (e.g. `group:eng#member`), not
only a plain id — equality compares the full structured subject, not just an
object id.

Any storage adapter's underlying comparison (e.g. a database column
collation) must not be more permissive than this — a case-insensitive
collation would silently change the library's semantics and is not
conformant.

## Threading (`MemoryTupleStore`)

`MemoryTupleStore` satisfies the exact same contract as any other adapter,
including atomicity-as-visibility and the evaluation-scoped view required
above. A lock held only per individual read is **not** sufficient — it
would be released and reacquired between reads within the same `check()`,
which reproduces the exact snapshot-drift bug the view exists to prevent.

> **Non-normative implementation note:** the expected strategy is
>
> ```text
> acquire lock → copy the current tuple set → release lock → evaluate
> against the immutable copy for the rest of this check()
> ```
>
> The copy, not a re-acquired lock, is what gives the view its stability:
> no concurrent mutation can be observed mid-evaluation because the view no
> longer looks at live state at all once it's opened. This is a demo/test
> adapter with no throughput requirement, so copying the full tuple set per
> `check()` is an acceptable cost, not a compromise. Only "the view is
> stable for its lifetime" is part of the contract — the copy-based
> mechanism is one way to get there, not the requirement itself.


## Explicit non-goals (v1)

Stated as decisions, not omissions:

- **Bulk delete by pattern.** No "delete every tuple for `document:42`" in
  one call. v1 only deletes tuples the caller names explicitly. Cheap to
  declare now; without it, `delete_tuples` tends to grow into an accidental
  query language.
- **Tombstones / audit history.** "Who granted this access, and when" is a
  real need for authorization systems generally, but it is not this layer's
  job in v1 — it also risks `PostgresTupleStore` accumulating metadata that
  `MemoryTupleStore` has no way to represent, breaking substitutability.
- **Pagination.** No public cursor/resume-token API for walking result sets
  across multiple calls. This is a narrower non-goal than it might sound:
  it does **not** exempt enumeration from being boundable per-call (see
  "Enumeration must be boundable" above) — "no pagination" and "no limit"
  are different decisions, and only the first is the non-goal.
