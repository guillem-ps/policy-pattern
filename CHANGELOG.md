# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- v1: `Model` / `compile()` / `CompiledModel`, the `Relation`/`Permission` split, relation rewrite operators
  (`Union`, `Intersection`, `Exclusion`, `TupleToUserset`), `Evaluator.check()` with `EvaluationBudget`
  (depth/nodes/reads), the `TupleStore` port, and the `MemoryTupleStore` adapter.
