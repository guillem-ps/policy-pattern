# Contributing

Contributions are welcome once the initial semantic model and public interfaces stabilize. Until then, expect
significant churn — check [`docs/architecture.md`](../docs/architecture.md) § Scope before proposing a feature that
might already be planned or explicitly out of scope.

Participation in this project is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).

Because this library participates in authorization decisions, changes affecting semantics or security should
include:

- explicit behavioral reasoning,
- corresponding tests,
- compatibility considerations,
- updates to the relevant specification (`docs/semantics.md`, `docs/architecture.md`) if behavior changed.

Security vulnerabilities should be reported according to [`SECURITY.md`](../SECURITY.md), not through a public issue.

## Testing strategy

Authorization behavior is tested at several levels:

- **Unit tests** — the relation rewrite evaluator is tested independently from storage: direct relationships,
  union, intersection, exclusion, tuple-to-userset, recursion, cycles, evaluation limits, error propagation.
- **Storage contract tests** — every `TupleStore` implementation runs against the same behavioral contract suite,
  so `MemoryTupleStore`, `PostgresTupleStore` (v2), and any future adapter stay semantically substitutable.
- **PostgreSQL integration tests** (v2) — the PostgreSQL adapter will be tested against a real PostgreSQL instance
  using Testcontainers. Database behavior is not mocked.
- **Security-oriented tests** — situations that could otherwise manufacture an incorrect authorization decision:
  storage failures, incomplete reads, truncated enumeration, concurrent mutations, snapshot drift, malformed
  relationship graphs, recursion limits.

Run locally with `make test` (or `make coverage` for a coverage report) — see the [Makefile](../Makefile) for every
available target.

## Pull requests

Use the PR template's checklist. Commit messages follow
[Conventional Commits](https://www.conventionalcommits.org).
