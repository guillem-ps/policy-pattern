# CHANGELOG


## v0.1.0 (2026-10-02)

### Bug Fixes

- Correct link to Code of Conduct in pull request template
  ([`48cbe07`](https://github.com/guillem-ps/policy-pattern/commit/48cbe07b9fa709cea532cec6d231418db3474fce))

- Rename `read_tuples` to `read_relation` for consistency in semantics documentation
  ([`9b944aa`](https://github.com/guillem-ps/policy-pattern/commit/9b944aafe1cfdce0629f3587c0a7c1ec7e618111))

- Solve typo in test identifier file name
  ([`51e0058`](https://github.com/guillem-ps/policy-pattern/commit/51e0058339eaa1cf5dbca5b4893f2128cd423125))

- Update action versions in workflow files for consistency
  ([`10386e3`](https://github.com/guillem-ps/policy-pattern/commit/10386e3c2cb29b7bb2ecb218150ead0203e7f1a5))

- Update documentation in PermissionExpression class to clarify operator composition
  ([`bb4e58d`](https://github.com/guillem-ps/policy-pattern/commit/bb4e58d3d72704d175d839bfde46639bc235b278))

- Update error codes for UnknownTypeError and UnknownNameError for consistency
  ([`5c967c5`](https://github.com/guillem-ps/policy-pattern/commit/5c967c54a63fd821d4e57c1a74602cd06bae3f9d))

- Update Gitleaks action to use the official action version for improved reliability
  ([`bc035d5`](https://github.com/guillem-ps/policy-pattern/commit/bc035d5dbe857d234267bad878a4b7736d16925b))

- Update permissions in CodeQL workflow to include actions read access
  ([`ea877d8`](https://github.com/guillem-ps/policy-pattern/commit/ea877d8080552df9228f1e9a54edafa9d75822cc))

- Update relative links in CONTRIBUTING.md for consistency
  ([`a25668c`](https://github.com/guillem-ps/policy-pattern/commit/a25668c6962fb5644ab9c91807105d2e55817e5c))

- **ci**: Disable CodeQL SARIF upload when unsupported
  ([`406407c`](https://github.com/guillem-ps/policy-pattern/commit/406407c8926217a019b01c0c9cc1aa1ceb1cb4bb))

Co-authored-by: guillem-ps <58363308+guillem-ps@users.noreply.github.com>

- **ci**: Run gitleaks standalone instead of gitleaks-action
  ([`19c532c`](https://github.com/guillem-ps/policy-pattern/commit/19c532caf62ab2efa21383e8b2e4d1972770bc9b))

- **ci**: Update Gitleaks version to v8.27.0 for consistency with pre-commit configuration
  ([`1a5f773`](https://github.com/guillem-ps/policy-pattern/commit/1a5f7735ce60b7bf7a5a813c59489b6beb8d55ff))

- **ci**: Update workflows to support CI retriggering via 'retrigger-ci' label
  ([`0316f3b`](https://github.com/guillem-ps/policy-pattern/commit/0316f3bd127bfe531448092d25744f0d45c967e2))

- **docs**: Clarify restrictions on Type names and update Identifier documentation
  ([`1ec5a40`](https://github.com/guillem-ps/policy-pattern/commit/1ec5a400f2d238bd945693a9f257cfb8522d8707))

- **docs**: Clarify the coverage of storage and evaluation semantics in semantics.md
  ([`ba9255c`](https://github.com/guillem-ps/policy-pattern/commit/ba9255cbeae86f91faca116b1a42695162757bf3))

- **docs**: Remove outdated comments in semantics.md and tuple_store.py for clarity
  ([`796f02e`](https://github.com/guillem-ps/policy-pattern/commit/796f02e750ca831c6204b5ceb4726631a542c96d))

- **docs**: Update project status and improve documentation structure in README.md
  ([`e0f7036`](https://github.com/guillem-ps/policy-pattern/commit/e0f7036ac9c65c8dc10ca416e0ea308937c68126))

- **docs**: Update PULL_REQUEST_TEMPLATE for clarity and completeness
  ([`e24978c`](https://github.com/guillem-ps/policy-pattern/commit/e24978c083e5eaa7fcb61d74ca875f8fa4635b8c))

- **errors**: Correct wording in error documentation and identifier class description
  ([`d68191e`](https://github.com/guillem-ps/policy-pattern/commit/d68191e01e8da2f1ee744b7f6231d25301e1fd3a))

- **evaluator**: Enforce allowed_subject_types and deterministic ordering
  ([`9cdc05a`](https://github.com/guillem-ps/policy-pattern/commit/9cdc05ab6cd8fb4495314bed72326e98c23e3d9e))

- **evaluator**: Include type representation in error messages for max depth, max nodes, and unknown
  expression types
  ([`ccc6aa1`](https://github.com/guillem-ps/policy-pattern/commit/ccc6aa1df7bc97561446b19c7b4c661193c2bf4a))

- **model**: Validate TupleToUserset.computed against every traversal target
  ([`c39472b`](https://github.com/guillem-ps/policy-pattern/commit/c39472b946ac5b22d51c97160d28d88af12e9685))

- **release**: Update GitHub token to use RELEASE_TOKEN for semantic release
  ([`223b6da`](https://github.com/guillem-ps/policy-pattern/commit/223b6da3569f4b291b6ae57b3c0aafe6e75bd652))

- **secrets**: Update permissions in secrets.yaml to include pull-requests read access
  ([`28c95f2`](https://github.com/guillem-ps/policy-pattern/commit/28c95f2999c7af0cbaccd0dab7d1edf1f8eadbc7))

- **tests**: Add test for Type name containing '#' to raise InvalidIdentifierError
  ([`583a42b`](https://github.com/guillem-ps/policy-pattern/commit/583a42bedfd307b1e439529d2781863b678e793c))

### Build System

- Add initial project skeleton and dependency lockfile
  ([`63175e8`](https://github.com/guillem-ps/policy-pattern/commit/63175e860b6ab2da41289b99424bb547f222c21c))

Introduce the policy_pattern package skeleton, pyproject.toml build config (uv_build,
  dependency-groups, pytest markers), pre-commit hooks, and locked dependencies (uv.lock + exported
  requirements files) so the environment is reproducible before application code lands.

- **Makefile**: Improve coverage command to preserve pass/fail status
  ([`23520d8`](https://github.com/guillem-ps/policy-pattern/commit/23520d868cdb73486b1ebc499cd68c9aab4f70fe))

- **pyproject**: Build: configure ruff, ty, and coverage tooling
  ([`bab3d0c`](https://github.com/guillem-ps/policy-pattern/commit/bab3d0c2591f627724f5cefb7fc6aba18ddd6b5b))

### Chores

- Retrigger CI
  ([`fbf8f04`](https://github.com/guillem-ps/policy-pattern/commit/fbf8f049081bb4ef58208413a0362ce74b854176))

### Continuous Integration

- Add CI workflow with testing, linting, and secret scanning jobs
  ([`9d76ddc`](https://github.com/guillem-ps/policy-pattern/commit/9d76ddced6260bee3ca213a4ee5ada3fe1d8c467))

- **hooks**: Add pre-commit file config
  ([`644d030`](https://github.com/guillem-ps/policy-pattern/commit/644d03007bceaf634eab4d701ce1b2c1efb9e928))

- **Makefile**: Create makefile for tests and lint alias
  ([`8004f0f`](https://github.com/guillem-ps/policy-pattern/commit/8004f0fb99f4c5184bd215ac45988be013ee67e0))

- **py312**: Update Python version support to include 3.12
  ([`33ed0b2`](https://github.com/guillem-ps/policy-pattern/commit/33ed0b2d5bcf694b276d433a24a674488f3d9709))

### Documentation

- Add CITATION.cff
  ([`caccff2`](https://github.com/guillem-ps/policy-pattern/commit/caccff225181d7e40d1602aa8539d4e534c443a0))

Adds standard citation metadata (authors, abstract, keywords, Apache-2.0 license) so the project can
  be properly cited once published. version/date-released and PyPI url intentionally omitted — not
  released yet.

- Add initial specification, license, and security policy
  ([`da3ff85`](https://github.com/guillem-ps/policy-pattern/commit/da3ff85935a77fc98ec246be06c024a3a6a8a15b))

- Clarify docstring explanations for Subject and SubjectSet
  ([`7917c9f`](https://github.com/guillem-ps/policy-pattern/commit/7917c9f440abad853ba7125bb079d82f6d85be47))

- Enhance docstrings to clarify validation of components
  ([`4e2f36a`](https://github.com/guillem-ps/policy-pattern/commit/4e2f36a51fb3cade9ee74f3ac0a64699cc8a7d55))

- **direct_subject**: Enhance docstring with detailed explanation and examples
  ([`9185204`](https://github.com/guillem-ps/policy-pattern/commit/9185204d34cc042a95b14c21bfe8ec3ded0a5a06))

- **errors**: Correct class name from PolicyPatternBaseError to BaseError in documentation
  ([`c14a2df`](https://github.com/guillem-ps/policy-pattern/commit/c14a2df4b5039e9ff61739ec9e41740bb22f0d1e))

- **semantics**: Update example identifiers in semantics document
  ([`b0fed6b`](https://github.com/guillem-ps/policy-pattern/commit/b0fed6b93635cd9e89d0e51f8199cc38de48afb4))

### Features

- Add Code of Conduct and update contributing guidelines
  ([`2b4ffe4`](https://github.com/guillem-ps/policy-pattern/commit/2b4ffe41a97d2767ec7919d8e642e94f5d32a24f))

- Add ModelValidationError and CompiledModel classes with tests for authorization schema
  ([`a38b3b1`](https://github.com/guillem-ps/policy-pattern/commit/a38b3b1d6ebd2d14893dc4cdd35b022e697da806))

- Add PermissionExpression and related classes for permission evaluation
  ([`5741589`](https://github.com/guillem-ps/policy-pattern/commit/57415893ce1654936e61f7b85bee775eb34da985))

- Add release pipeline and changelog for automated versioning
  ([`b43c207`](https://github.com/guillem-ps/policy-pattern/commit/b43c207d51ab999372288b2655badb93cce49ef5))

- **agents**: Add AGENTS.md for project overview and development workflow
  ([`32d883a`](https://github.com/guillem-ps/policy-pattern/commit/32d883a69fd9dc40a944d0e88f2e4ebe4b9b5ecd))

- **direct_subject**: Add DirectSubject class and corresponding tests
  ([`67187c9`](https://github.com/guillem-ps/policy-pattern/commit/67187c94cc4008297ed2aca3e0ca3afb63ca87eb))

- **docs**: Add comprehensive architecture document outlining authorization model and evaluator
  ([`62601da`](https://github.com/guillem-ps/policy-pattern/commit/62601da340a9ae42828d004ebfb4ea2dd416cbcf))

- **docs**: Add CONTRIBUTING.md to outline contribution guidelines and testing strategy
  ([`9934ab9`](https://github.com/guillem-ps/policy-pattern/commit/9934ab9048e31be0f992e8d2d6477cc943bdced0))

- **docs**: Add detailed Usage Guide and documentation structure for policy-pattern
  ([`b91a53e`](https://github.com/guillem-ps/policy-pattern/commit/b91a53eda4f6397a79068f564bdfd2977e6ef24d))

- **errors): feat(errors**: Add base error class and error codes documentation
  ([`139672b`](https://github.com/guillem-ps/policy-pattern/commit/139672b78eaa9ddc6dcc8e0a0cb145699c420d93))

Provide a basic class error exception for LSP-diagnostic-style contract (code + severity + related).

- **evaluator**: Add new error classes for evaluation handling and update imports
  ([`67ea5aa`](https://github.com/guillem-ps/policy-pattern/commit/67ea5aa098857b250a829e26ae7fccf60588ef80))

- **funding**: Add FUNDING.yaml to support GitHub sponsorship
  ([`030e91a`](https://github.com/guillem-ps/policy-pattern/commit/030e91a31e438f91369fd9616c4e1ffa9a0362ce))

- **github**: Add CODEOWNERS file to define code ownership
  ([`47e8be0`](https://github.com/guillem-ps/policy-pattern/commit/47e8be087036c66c3e52902eca7c2a0d39f1f07b))

- **identifier**: Implement Identifier class with validation and error handling
  ([`1d4cc95`](https://github.com/guillem-ps/policy-pattern/commit/1d4cc95ba3caff85bbf2ecfbc31e660bad76313d))

Introduces Identifier (bounded length, printable-only, no leading/trailing whitespace) as the first
  Value Object per docs/semantics.md's identifier bounds. Test suite covers both the validation
  rules and the Value Object contract itself (equality, hash, immutability).

- **issue-templates**: Add bug report and feature request templates
  ([`bd7f9cc`](https://github.com/guillem-ps/policy-pattern/commit/bd7f9ccd7cf23ea516687acf9526c2180da5e9da))

- **issues**: Add issue templates for questions and configuration
  ([`9e24369`](https://github.com/guillem-ps/policy-pattern/commit/9e24369cb3db3c4e428c47c1efe57d3264e418e1))

- **memory**: Implement in-memory TupleStore adapter with tests with a determinism probe between
  processes
  ([`dd6cc20`](https://github.com/guillem-ps/policy-pattern/commit/dd6cc20ea0c9f6cc625fec5c466ed28392243084))

- **model**: Enhance Type validation for relation and permission names with corresponding tests
  ([`eb3f262`](https://github.com/guillem-ps/policy-pattern/commit/eb3f262fc9dc975c422d5f2d23e8a9afb3cac765))

- **model**: Validate Type name consistency in compile method and add corresponding test
  ([`07d88ae`](https://github.com/guillem-ps/policy-pattern/commit/07d88aec1eb0e12d37ecf420ce5933926ede002b))

- **mutation**: Add Mutation class and InvalidMutationError for authorization store operations
  ([`73c100a`](https://github.com/guillem-ps/policy-pattern/commit/73c100ab3514bddc463e6fd83482eda323409ee4))

- **object_reference**: Add ObjectReference class with validation and tests
  ([`12cacf1`](https://github.com/guillem-ps/policy-pattern/commit/12cacf1132d1647a8590c501463cb5c27d632901))

- **ports**: Add TupleStore and View storage ports
  ([`288308e`](https://github.com/guillem-ps/policy-pattern/commit/288308e9726af9fa419ac4c4f3cfcfc00cfc8817))

- **pre-commit**: Add Unresolved Clarification Checker hook
  ([`299f541`](https://github.com/guillem-ps/policy-pattern/commit/299f54127668ecc1de0e14f4987b711229247033))

- **relation**: Add InvalidRelationError and tests for Relation class
  ([`305f822`](https://github.com/guillem-ps/policy-pattern/commit/305f822aa4f486fa78a1e5f4470e5ac13b9f9222))

- **subject**: Add Subject type alias for authorization graph
  ([`5c8b3b9`](https://github.com/guillem-ps/policy-pattern/commit/5c8b3b9eedbd819ed99a2ab8255ba981ebb81072))

- **subject_set**: Add SubjectSet class and corresponding tests
  ([`cd4ac3e`](https://github.com/guillem-ps/policy-pattern/commit/cd4ac3e0e1420019d233dcfc0c3f28879247e3d9))

- **tuple**: Add Tuple class for representing relationship facts in the authorization graph
  ([`c1de316`](https://github.com/guillem-ps/policy-pattern/commit/c1de316c65db83797f77fb86f153f0377cecf73c))

- **v2**: Add section for unscheduled ideas beyond v2
  ([`17eebee`](https://github.com/guillem-ps/policy-pattern/commit/17eebeeb04803c94fcc0906193785dff75fb9b35))

- **validation**: Enforce unique names for relations and permissions in Type validation
  ([`6bca801`](https://github.com/guillem-ps/policy-pattern/commit/6bca801d62ca5deb4289b13c08dd5b932c95fe28))

- **validation**: Implement shared type validation for Model and CompiledModel with tests
  ([`c0a32fc`](https://github.com/guillem-ps/policy-pattern/commit/c0a32fc63296b8d04a8d3152eb52b5cb4e5bd25f))

- **workflows**: Add CodeQL, lint, secret scanning, and test pipelines
  ([`8a16637`](https://github.com/guillem-ps/policy-pattern/commit/8a166370bc75ec19a36b2bb6526ec1d1786eb674))

### Refactoring

- **errors**: Remove severity attribute from BaseError class
  ([`7e30833`](https://github.com/guillem-ps/policy-pattern/commit/7e308338d61194ae343c637084d2eaf0093340ed))

### Testing

- Add unit tests for Union, Intersection, and Exclusion classes
  ([`83dc860`](https://github.com/guillem-ps/policy-pattern/commit/83dc8608ef2390a2519ca77ca4884239107d28d1))

- **identifier**: Add check for FrozenInstanceError on field assignment
  ([`d3039c2`](https://github.com/guillem-ps/policy-pattern/commit/d3039c2a3fedcd565f7ca042b058f004b54ad8bf))

- **object_reference**: Add inequality and hash consistency tests for ObjectReference class
  ([`fc021aa`](https://github.com/guillem-ps/policy-pattern/commit/fc021aa5c91267423cb7d5479c1dbea8e3dd3e12))
