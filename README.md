# policy-pattern

> A small, embeddable ReBAC authorization engine for Python, inspired by Google Zanzibar.

<p align="center">
    <a href="https://github.com/guillem-ps/policy-pattern/actions/workflows/test.yaml" target="_blank">
        <img src="https://github.com/guillem-ps/policy-pattern/actions/workflows/test.yaml/badge.svg" alt="Test Pipeline">
    </a>
    <a href="https://github.com/guillem-ps/policy-pattern/actions/workflows/lint.yaml" target="_blank">
        <img src="https://github.com/guillem-ps/policy-pattern/actions/workflows/lint.yaml/badge.svg" alt="Lint Pipeline">
    </a>
    <a href="https://codecov.io/gh/guillem-ps/policy-pattern" target="_blank">
        <img src="https://codecov.io/gh/guillem-ps/policy-pattern/graph/badge.svg" alt="Coverage Pipeline">
    </a>
    <a href="pyproject.toml" target="_blank">
        <img src="https://img.shields.io/badge/version-0.1.0-blue" alt="Package Version">
    </a>
    <a href="pyproject.toml" target="_blank">
        <img src="https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue" alt="Supported Python Versions">
    </a>
</p>

`policy-pattern` is a standalone Python library for relationship-based access control (ReBAC). It models
authorization as relationships between subjects and objects and evaluates those relationships through composable
authorization rules.

- **No authorization server**
- **No required framework**
- **No required database**
- **No network hop**

The library is designed to be embedded directly into Python applications that need richer authorization semantics
than traditional role-based access control.

> **Status:** v1 is code-complete — model, `compile()`, the storage port, `MemoryTupleStore`, and the `Evaluator`
> all exist and are tested.

See [Architecture § Scope](docs/architecture.md#scope) for what's planned (v1.x/v2) and unscheduled ideas.

---

## Table of Contents

* [Example](#example)
* [Documentation](#documentation)
* [Contributing](#contributing)
* [License](#license)
* [References](#references)

---

## Example

```python
model = Model()
model.types["document"] = Type(
    name="document",
    relations={
        "owner": Relation(allowed_subject_types=("user",)),
        "parent": Relation(allowed_subject_types=("folder",)),
    },
    permissions={
        "viewer": Union(left=Reference(name="owner"), right=TupleToUserset(tupleset="parent", computed="viewer")),
    },
)
compiled = model.compile()

evaluator = Evaluator(model=compiled, store=store)
evaluator.check(alice, "viewer", document_42)
```

`viewer` here means "the document's own owner, or the owner of whatever folder it lives in" — a document under
`folder:engineering` inherits access from that folder without copying a permission onto every document.

See the [Usage Guide](docs/usage/README.md) for the full, runnable walkthrough — every rewrite operator, nested
groups, `EvaluationBudget`, and error handling.

---

## Documentation

The repository uses specifications and architecture documents as part of the implementation contract — they
describe **what must be true**, independent of any one adapter's implementation.

```text
docs/
├── README.md        — documentation index, start here
├── usage/README.md  — worked examples for every rewrite operator, budgets, error handling
├── architecture.md  — the model shape, compile(), the storage port, the evaluator, and scope/roadmap
├── semantics.md     — the storage contract every TupleStore adapter must satisfy
└── errors.md        — the PPxxx error code ranges and what each one means
```

Start with the [Usage Guide](docs/usage/README.md) to see the library working end to end, then
[Architecture](docs/architecture.md) to understand why the model is shaped the way it is.

---

## Contributing

We love community help! Before you open an issue or pull request, please read:

* [How to Contribute](.github/CONTRIBUTING.md)
* [Code of Conduct](.github/CODE_OF_CONDUCT.md)
* [Security Policy](SECURITY.md)

---

## License

Licensed under the [Apache License 2.0](LICENSE.md).

---

## References

The design is influenced by authorization systems and literature including:

* [Google Zanzibar](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/)
* [OpenFGA](https://openfga.dev)
* [SpiceDB](https://github.com/authzed/spicedb) / [AuthZed](https://authzed.com)

`policy-pattern` is an independent project and is not an implementation of, or affiliated with, those projects.
