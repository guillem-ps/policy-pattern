# Security Policy

## Project status

`policy-pattern` is published to [PyPI](https://pypi.org/project/policy-pattern/)
and versioned via semantic releases (currently pre-`1.0`). No deployed
consumer is confirmed yet, but the package is installable and this
policy applies to every published version, not just a future one.

## Scope

This library sits directly on the authorization decision path, so its
security bar is higher than a typical dependency. In scope for
reports: any input that produces an incorrect `check()` result
(false allow is critical; false deny is a correctness bug but still
reportable), tuple storage adapters (in-memory and Postgres) leaking
or corrupting data across namespaces/tenants, and denial-of-service
vectors in the relation rewrite evaluator (e.g. unbounded recursion
through tuple-to-userset rules).

Out of scope: authentication logic (login, password handling, session
management, token issuance) is not part of this library and is not
covered here — this library only answers "is this action allowed,"
never "who is this."

## Reporting a vulnerability

Do **not** open a public GitHub issue for security reports, and do not
publish a proof-of-concept before a fix is available — a bug in this
library affects every consumer's authorization decisions.

Use [GitHub Security Advisories](https://github.com/guillem-ps/policy-pattern/security/advisories/new)
for this repository, or email the maintainer directly if advisories
are unavailable. Include a minimal reproduction (subject/relation/
object tuples and the rewrite rules involved) where possible.

## Response expectations

This project is independently maintained, without a dedicated support
contract — there is no SLA. Given the security-sensitive nature of an
authorization engine, correctness reports are prioritized over feature
work. Reports get a best-effort acknowledgment and a fix or mitigation
plan communicated back to the reporter before any public disclosure.

## Supported versions

Pre-`1.0`: only the latest published release on PyPI is supported. A
reported vulnerability is fixed in a new release, not backported to an
older `0.x` line. This section will list explicit supported lines once
`1.0` ships.
