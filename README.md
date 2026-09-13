# policy-pattern

> A small, embeddable ReBAC authorization engine for Python, inspired by Google Zanzibar.

`policy-pattern` is a standalone Python library for relationship-based access control (ReBAC).

It models authorization as relationships between subjects and objects and evaluates those relationships through composable authorization rules.

No authorization server.
No required framework.
No required database.
No network hop.

The library is designed to be embedded directly into Python applications that need richer authorization semantics than traditional role-based access control.

> **Status:** design and specification phase. The public contracts and authorization semantics are being defined before the implementation is written.

---

## Table of Contents

* [Why policy-pattern?](#why-policy-pattern)
* [Example](#example)
* [Core concepts](#core-concepts)
* [Architecture](#architecture)
* [Storage](#storage)
* [Correctness and semantics](#correctness-and-semantics)
* [Planned v1](#planned-v1)
* [Roadmap](#roadmap)
* [Permanent scope boundary](#permanent-scope-boundary)
* [Testing strategy](#testing-strategy)
* [Security](#security)
* [Documentation](#documentation)
* [Contributing](#contributing)
* [License](#license)

---

## Why policy-pattern?

Traditional RBAC works well when authorization can be expressed as:

```text
role -> permission
```

Real applications often need decisions that depend on relationships between resources:

```text
user:7 is owner of folder:engineering

document:42 belongs to folder:engineering

owners of the parent folder may view the document
```

The authorization question is therefore not simply:

```text
Does user:7 have the "viewer" role?
```

but:

```text
Can user:7 view document:42
according to the relationships and rules in the authorization model?
```

`policy-pattern` represents those relationships as tuples and evaluates them as a graph.

This style of authorization is useful for domains involving nested resources, organizations, teams, groups, repositories, folders, documents, projects, and delegated permissions.

---

## Example

A conceptual relationship graph might contain:

```text
folder:engineering#owner@user:7

document:42#parent@folder:engineering
```

with an authorization model equivalent to:

```text
document.viewer =
    document.owner
    OR
    document.parent->owner
```

Then:

```python
engine.check(
    subject="user:7",
    relation="viewer",
    object="document:42",
)
```

would evaluate whether `user:7` belongs to the `viewer` userset for `document:42`.

The exact Python API is still being designed.

---

## Core concepts

### Relationship tuples

Relationships are structurally represented as:

```text
(subject, relation, object)
```

For example:

```text
subject  = user:7
relation = owner
object   = document:42
```

A human-readable Zanzibar-style representation is:

```text
document:42#owner@user:7
```

The structured representation is authoritative. Text serialization and its escaping rules are specified separately.

Subjects may also refer to usersets rather than individual identities.

For example:

```text
group:engineering#member
```

can itself participate as a subject in another relationship.

---

### Authorization model

Stored relationships and authorization rules are deliberately separate.

The `AuthorizationModel` defines:

* object types,
* relations,
* valid subject types,
* computed relationships,
* relation rewrite expressions.

Conceptually:

```text
AuthorizationModel
        |
        v
     Evaluator <------ TupleStore
        |
        v
   authorization
      decision
```

The storage layer does not interpret the authorization model.

---

### Relation rewrites

The v1 evaluator is intended to support the fundamental ReBAC operations:

```text
union
intersection
exclusion
tuple-to-userset
```

Conceptually:

```text
viewer = owner | editor
```

```text
privileged = employee & security_trained
```

```text
viewer = member - blocked
```

and:

```text
viewer = parent->owner
```

The final semantics of these operators are defined independently of their Python implementation.

---

## Architecture

`policy-pattern` follows a ports-and-adapters / hexagonal design.

```text
                    AuthorizationModel
                           |
                           v
                   +---------------+
subject ---------->|               |
relation ---------->|   Evaluator   |----> decision
object ------------>|               |
                   +-------+-------+
                           |
                           v
                      TupleStore
                      /        \
                     /          \
             MemoryTupleStore  PostgresTupleStore
```

The evaluator depends on the `TupleStore` abstraction rather than a database implementation.

Consumers of `policy-pattern` therefore do not depend on PostgreSQL, and the authorization engine does not depend on application frameworks such as FastAPI or Django.

---

## Storage

`TupleStore` is a schema-agnostic storage port for authorization tuples.

The v1 contract includes:

* set semantics — duplicate tuples do not exist,
* idempotent writes and deletes,
* atomic mutation sets,
* exact tuple lookup,
* enumeration by `(object, relation)`,
* bounded enumeration,
* explicit detection of truncated results,
* read-after-write consistency,
* evaluation-scoped consistent snapshots,
* strict distinction between empty results and storage failures.

An authorization decision that performs multiple storage reads must observe one logically consistent store snapshot.

The initial adapters are planned to be:

* `MemoryTupleStore` — tests, examples, and local usage;
* `PostgresTupleStore` — durable production storage.

All adapters must satisfy the same shared contract test suite.

---

## Correctness and semantics

Authorization correctness is treated as a security property.

A **false allow** — granting access when the model does not authorize it — is considered a critical defect.

The project therefore defines observable semantics before adapter-specific implementation details.

Examples of invariants already specified include:

```text
storage failure != empty result

truncated enumeration != complete enumeration

one check == one consistent storage snapshot
```

Storage semantics are documented separately in:

```text
docs/semantics.md
```

Evaluation semantics will define the behavior of:

* direct relationships,
* computed relationships,
* union,
* intersection,
* exclusion,
* tuple-to-userset,
* recursive evaluation,
* cycle handling,
* bounded evaluation,
* authorization errors.

Implementation details such as PostgreSQL indexes, transaction mechanisms, and adapter-specific optimizations are intentionally not part of the cross-adapter semantic contract.

---

## Planned v1

The first usable release is intentionally narrow.

```text
v1
├── structured relationship tuples
├── AuthorizationModel
├── direct relationships
├── union
├── intersection
├── exclusion
├── tuple-to-userset
├── recursive Check evaluation
├── cycle protection
├── bounded evaluation
├── MemoryTupleStore
├── PostgresTupleStore
├── storage contract tests
└── PostgreSQL integration tests
```

The goal is not to reproduce every feature of Google Zanzibar, OpenFGA, or SpiceDB.

The goal is to provide a small authorization core with understandable semantics and strong correctness guarantees.

---

## Roadmap

Possible post-v1 capabilities include:

### Reverse lookup

```text
ListObjects(subject, relation, object_type)
```

For questions such as:

```text
Which documents can user:7 view?
```

Reverse lookup requires different storage access patterns from forward `Check` evaluation and is deliberately excluded from the v1 storage port.

### Contextual tuples

Request-scoped relationships that participate in an authorization decision without being persisted.

These may be useful for contextual information derived from a request, token, or application state.

### Explain / trace

A diagnostic representation of how an authorization decision was reached.

For example:

```text
user:7
  -> owner of folder:engineering
  -> parent of document:42
  -> therefore viewer of document:42
```

Any explanation API must be designed carefully to avoid leaking sensitive authorization graph information.

### Batch checks

Evaluate multiple authorization questions while safely reusing evaluation state where possible.

### Model versioning

Explicit versioning and migration of authorization models as applications evolve.

### Advanced consistency

Consistency tokens or other mechanisms for applications that require authorization decisions tied to specific externally-observed versions of state.

### Operational capabilities

Potential later capabilities include:

* bulk tuple deletion,
* audit-oriented metadata or history,
* change notifications.

These are not part of v1.

---

## Permanent scope boundary

`policy-pattern` is an **embedded Python authorization library**.

It will not evolve into a centralized authorization server.

Running a horizontally-scaled authorization service with its own:

```text
HTTP / gRPC API
distributed caches
replication
multi-region consistency
service discovery
cross-language clients
```

is a different architectural problem.

Projects such as OpenFGA and SpiceDB are designed for that class of system.

`policy-pattern` intentionally targets another use case:

> A Python application that wants ReBAC authorization semantics without operating a separate authorization service.

This is a permanent product boundary rather than a missing roadmap feature.

---

## Testing strategy

Authorization behavior is tested at several levels.

### Unit tests

The relation rewrite evaluator is tested independently from storage.

Coverage includes:

* direct relationships,
* union,
* intersection,
* exclusion,
* tuple-to-userset,
* recursive relationships,
* cycles,
* evaluation limits,
* error propagation.

### Storage contract tests

Every `TupleStore` implementation runs against the same behavioral contract suite.

The goal is that:

```text
MemoryTupleStore
PostgresTupleStore
FutureTupleStore
```

remain semantically substitutable.

### PostgreSQL integration tests

The PostgreSQL adapter is tested against a real PostgreSQL instance using Testcontainers.

Database behavior is not mocked.

### Security-oriented tests

Tests explicitly target situations that could otherwise manufacture an incorrect authorization decision, including:

* storage failures,
* incomplete reads,
* truncated enumeration,
* concurrent mutations,
* snapshot drift,
* malformed relationship graphs,
* recursion limits.

---

## Security

Authorization libraries sit directly on a security boundary.

`policy-pattern` therefore treats security failures differently from ordinary library defects.

In particular:

> An incomplete, failed, or ambiguous evaluation must never accidentally become an authorization grant.

Storage errors, evaluation limits, malformed models, and internal evaluation failures remain distinguishable from ordinary authorization denial.

See [`SECURITY.md`](./SECURITY.md) for the vulnerability disclosure policy.

---

## Documentation

The repository uses specifications and architecture documents as part of the implementation contract.

Planned documentation includes:

```text
docs/
├── semantics.md
├── authorization-model.md
├── evaluation-semantics.md
├── architecture/
│   └── ADR-*.md
├── postgres.md
└── examples/
```

The specifications describe **what must be true**.

Adapter and implementation documents describe **how a particular implementation makes it true**.

---

## Project status

The project is currently in the **design phase**.

The repository intentionally contains specification and architecture work before application code.

Current work focuses on:

```text
✓ storage semantics
→ authorization model
→ evaluation semantics
→ public API contract
→ implementation
```

The specification may evolve before the first stable release.

Once v1 is released, semantic compatibility will be treated as part of the public API.

---

## Contributing

Contributions will be welcome once the initial semantic model and public interfaces stabilize.

Because this library participates in authorization decisions, changes affecting semantics or security should include:

* explicit behavioral reasoning,
* corresponding tests,
* compatibility considerations,
* updates to the relevant specification or ADR.

Security vulnerabilities should be reported according to [`SECURITY.md`](./SECURITY.md), not through a public issue.

---

## License

Licensed under the [Apache License 2.0](./LICENSE.md).

---

## References

The design is influenced by authorization systems and literature including:

* Google Zanzibar
* OpenFGA
* SpiceDB / AuthZed

`policy-pattern` is an independent project and is not an implementation of, or affiliated with, those projects.
