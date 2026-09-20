# Error codes

Every `policy_pattern` exception is a `BaseError` shaped after
the [LSP Diagnostic](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#diagnostic)
model — a real, developer-facing standard for reporting errors and
warnings, adapted for a library instead of an editor/API client.

Deliberately in-process only — no serialization boundary in v1 (no HTTP,
no API layer in the core; see `docs/architecture.md`). If a consumer
(`iam-service`) ever needs to serialize one of these across a boundary,
that consumer's own translation layer does it — `policy_pattern` itself
never emits JSON/HTTP-shaped errors.

`related` replaces LSP's `relatedInformation` (a list of
`{location, message}` pairs pointing at source code) — a library has no
file/line span worth showing its caller, only a **model element** (a
field, a type, a relation name) worth naming. One string is enough for v1;
promote it to a structured field only if a single string stops being
enough in practice.

`code` is grep-able and documentable independent of message wording — a
caller can match on `err.code` without parsing free text.

Message format: interpolated values in `message`/`related` use Python's
`!r` conversion (`f"identifier {value!r} is invalid"`), not a custom
bracket convention — no automated hook enforces this, checked by hand on
review.*

In the future, it's necessary to automatise as a pre-commit hook, but for now, the human eye is enough.

## Ranges

```
PP0xx   identifier / value validation       (construction-time)
PP1xx   model validation                    (compile()-time only)
PP2xx   evaluation runtime                  (check()-time)
PP3xx   static analysis warnings            (v1.x, model.analyze())
PP9xx   storage / adapter errors            (only if a shared category is ever needed —
                                              adapters may raise their own errors instead,
                                              see docs/architecture.md § Errors)
```

A code is assigned once, per exception **class**, never per call site or
per instance — the message text can change freely without breaking
anything that matches on the code.

The registry of which code maps to which class lives in the code itself
(`code: ClassVar[str]` + the class's own docstring in
`policy_pattern/errors/`) — not duplicated here. A hand-maintained table
in this doc drifts the moment someone adds a class and forgets the row;
`grep -r 'code = "PP' policy_pattern/errors/` is always accurate, a
markdown table next to it is not.
