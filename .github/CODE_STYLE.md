# Code Style

Conventions this project enforces by hand — `ruff`/`ty`/pre-commit cover naming, imports, length, annotations, and docstring presence; see `pyproject.toml` and `.pre-commit-config.yaml` for those.

## Errors

| Do | Don't |
|---|---|
| Raise `policy_pattern`'s own domain errors via `BaseError(message=..., related=...)` | Raise a bare positional string, or a raw stdlib exception, for a `policy_pattern`-owned error |
| Let an adapter's dependency raise its own native exception across the storage boundary, unwrapped (`except Exception: rollback(); raise`) | Swallow a storage error into an empty result/`False` — see `docs/semantics.md` |
| Interpolate values with `!r`: `f"identifier {value!r} is invalid"` | Hand-bracket or leave values unescaped |

No shared `StorageError` base — see [`docs/architecture.md`](../docs/architecture.md) § Errors. `BaseError` wraps `policy_pattern`'s own errors; it is not a pass-through every adapter error must go through.

## Value Objects

```python
object.__setattr__(self, "relations", MappingProxyType(dict(self.relations)))  # copy first
```

| Do | Don't |
|---|---|
| `tuple`/`frozenset`/`MappingProxyType(dict(x))` — copy before wrapping | `list`/`dict` fields, or `MappingProxyType(x)` without copying `x` first |
| Delegate identifier-shaped fields to a throwaway `Identifier` in `__post_init__`, store the original `str` | Store `identifier.value` instead of the original string |

See [`docs/architecture.md`](../docs/architecture.md) for a worked example (`Identifier`, `ObjectReference`).

Minimum test coverage, every Value Object:

- [ ] equality
- [ ] inequality
- [ ] hash consistency
- [ ] one `with raises(FrozenInstanceError)` block **per field**
- [ ] independence from the original collection — mutate the caller's `dict`/`list` *after*
  construction, assert the Value Object didn't change (catches a dropped `dict(...)`/`list(...)` copy)

## File organization

- One concept per file, split the moment there's a second — the reason `errors/` and `models/` are  packages of small modules rather than single files.
- A helper a test uses goes above the test, not below.
- A helper shared across test files moves to a shared module (`tests/tuples_factory.py`), not  copy-pasted per file.

## Test doubles

| Lives in `tests/mother_classes/` | Stays local to its file |
|---|---|
| Shared across multiple test files | Used in exactly one file |
| Implements `TupleStore`/`View` | Implements a narrower protocol (e.g. `_db_protocols.py`'s `Cursor`/`Connection`/`ConnectionPool`) |

> Example: `tests/adapters/test_postgres_unit.py`'s `_CursorDouble`/`_PoolDouble`/etc. — one file, one protocol, stay put.

## Docstrings

Every function — public or private — carries `Args:`/`Returns:`/`Raises:`. `Raises:` lists the
function's **own contract** exceptions, never a dependency's entire exception hierarchy propagating
unchanged through it (see § Errors).

```python
def test_migrated_table_matches_schema_contract(postgres_pool: ConnectionPool) -> None:
    """Check the actual PostgreSQL columns, primary key, and collations.

    Args:
        postgres_pool (ConnectionPool): A connection pool to the PostgreSQL database.

    Returns:
        None

    Raises:
        AssertionError: If the actual schema does not match the expected schema.
    """
```

Forward-looking, not a retrofit — adopted 2026-10-29, migrated file by file as touched.

## Example data

`alice`, `bob`, `user:1` — never a real name. Real identity only in `LICENSE.md`/`CITATION.cff`/`pyproject.toml` `authors`/README copyright.

## Reference projects

Used while writing this one. Never named in anything that ships.

## Before you commit

```bash
uv run ruff format
uv run ruff check
uv run ty check policy_pattern
uv run pytest
```

Full detail: [`AGENTS.md`](../AGENTS.md) § Development Workflow.
