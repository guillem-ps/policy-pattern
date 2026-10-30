# Testing

How this project is tested, and what every test is expected to prove. For lint/type checks, see [`AGENTS.md`](AGENTS.md) § Development Workflow.

## Commands, by intent

| Intent | Command |
|---|---|
| Full suite | `uv run pytest` (or `make test`) |
| Fast local loop (no Docker, no slow tests) | `uv run pytest -m "not integration and not slow"` |
| Integration (today: PostgreSQL via Docker; any future adapter follows the same marker) | `uv run pytest -m integration` |
| Storage contract suite, against every adapter | `uv run pytest tests/contract/` |
| One file | `uv run pytest tests/path/to_test.py` |
| One test | `uv run pytest -k "expression"` |
| Every supported Python version (3.12/3.13/3.14) | `make test-all` |

> `pytest-randomly` shuffles module/class/test order every run — a suite whose pass/fail depends on execution order has a hidden ordering dependency. Reproduce a run with `uv run pytest --randomly-seed=<seed>` (printed at the top of every run); `--randomly-seed=last` reuses the previous one.

## What to test, by kind

| Kind | Against | Notes |
|---|---|---|
| Unit | Behavior in isolation from storage | Every Value Object also carries [`CODE_STYLE.md`](.github/CODE_STYLE.md) § Value Objects' minimum |
| Integration / end-to-end | The adapter's real backing service, via testcontainers | Never a mock of the storage port |
| Contract (`tests/contract/`) | Every adapter | A green run on one adapter alone proves nothing about another |

Never mock the authorization engine itself in a test exercising `check()`/`check_many()`/the evaluator — that's exactly the component a security bug would hide behind. 
  
See  [`docs/semantics.md`](docs/semantics.md) for why.

## TDD is mandatory

1. **RED** — write a test proving the functionality doesn't exist yet; run it, confirm it fails for the expected reason, not an unrelated one (a typo, a missing import).
2. **YELLOW** — implement the new functionality: the minimum code that makes the test pass.
3. **GREEN** — confirm the test passes and the objective is resolved optimally, not just technically; run the full suite before calling the task finished.

## Definition of done

A green suite is not, by itself, evidence a change is verified. If inverting the behavior under test would leave the suite green, that behavior is untested, regardless of how many tests pass — a view that reads live store state instead of its own copy still satisfies a naive read-after-write test.
