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

See [`TESTING.md`](../TESTING.md) for the full testing guide. Run locally with `make test` (or `make
coverage` for a coverage report) — see the [Makefile](../Makefile) for every available target.

## Pull requests

Use the PR template's checklist. Commit messages follow
[Conventional Commits](https://www.conventionalcommits.org).

## Force-retriggering CI on an open PR

`test.yaml`, `lint.yaml`, `secrets.yaml`, and `codeql.yaml` also run whenever the `retrigger-ci` label is
added to a PR (the `if:` guard on each job ignores any other label, so normal triage labels like `bug` never
trigger a run). Add it from the PR page, or with `gh pr edit <PR#> --add-label retrigger-ci`.

A label can't fire the same event twice in a row while it stays applied — remove it first if you need to
trigger again later.

This is for an **open PR's own checks** specifically — only a `labeled`/`synchronize`/`reopened` event on
that exact PR updates its check status.
