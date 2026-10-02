# policy-pattern Documentation

This directory contains deeper guides for using **policy-pattern** in real applications. The project root
[`README.md`](../README.md) is the quick overview; these pages define the actual contracts in detail.

## Guides

- [🧱 Usage Guide](usage/README.md): Building a `Model`, compiling it, writing tuples, and calling `check()` —
  worked examples for every rewrite operator (`Union`, `Intersection`, `Exclusion`, `TupleToUserset`) and for
  `EvaluationBudget`/error handling.
- [🏗️ Architecture](architecture.md): The model shape, `compile()`, the storage port, and the evaluator —
  how the pieces fit together and why.
- [📜 Semantics](semantics.md): The storage contract — mutation, read, and snapshot-consistency semantics every
  `TupleStore` adapter must satisfy. The source of truth for storage *behavior*, independent of any one adapter.
- [🚨 Errors](errors.md): The `PPxxx` error code ranges and what each one means.

## Recommended Reading Order

1. Start with the [Usage Guide](usage/README.md) to see the library working end to end.
2. Read [Architecture](architecture.md) to understand why the model is shaped the way it is.
3. Read [Semantics](semantics.md) before writing a new `TupleStore` adapter — it is the contract, not `MemoryTupleStore`'s
   implementation.
4. Use [Errors](errors.md) as a reference when handling a `policy_pattern` exception.

## Quick Safety Rule

A `check()` result is only as correct as the tuples and model behind it — `policy-pattern` never treats a storage
error, a truncated read, or an unresolved reference as an implicit deny or allow (see [Semantics](semantics.md) §
"Storage errors are not empty results"). If you see a `check()` swallowing an exception into `False` anywhere in your
own integration code, that is the one pattern this library is designed to make impossible to write by accident —
undo it.
