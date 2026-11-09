# CHANGELOG

<!-- version list -->

## v0.7.0 (2026-11-09)

### Bug Fixes

- **docs**: Correct link to TESTING.md in CONTRIBUTING.md
  ([`27c2c0c`](https://github.com/guillem-ps/policy-pattern/commit/27c2c0c0fb7db094d423f7bf922bc98f6b87ff92))

- **docs**: Update link to TESTING.md in CONTRIBUTING.md for consistency
  ([`bf02440`](https://github.com/guillem-ps/policy-pattern/commit/bf02440f75307fd9e6116acb009ca9e582242930))

### Chores

- Sync uv.lock and CITATION.cff date with released version
  ([`ad06423`](https://github.com/guillem-ps/policy-pattern/commit/ad06423f92dc37790071f1c5e0712e3ef1e4c268))

### Documentation

- Update docs cycle detection reference
  ([`1cce1b0`](https://github.com/guillem-ps/policy-pattern/commit/1cce1b0bc465c9c0202fe3ca7d6eb4e8fd3b88d9))

### Features

- **cycles_detection**: Enhance schema validation to detect permission cycles and add corresponding
  tests
  ([`4d61448`](https://github.com/guillem-ps/policy-pattern/commit/4d614483c0f61a04377edc85ceed31fa5d3300f1))


## v0.6.0 (2026-11-02)

### Bug Fixes

- **docs**: Update links to TESTING.md for consistency in documentation
  ([`e4a419f`](https://github.com/guillem-ps/policy-pattern/commit/e4a419f03a4d30e2bc3f55f6a8550f6fc5fe7866))

### Chores

- Sync uv.lock and CITATION.cff date with released version
  ([`dd64a25`](https://github.com/guillem-ps/policy-pattern/commit/dd64a253529ba353789bba2c8f3832be4b0800ca))

### Features

- **docs**: Add comprehensive testing guidelines to TESTING.md
  ([`f9918ba`](https://github.com/guillem-ps/policy-pattern/commit/f9918ba74c105e5eaba4141890ccd6051ce817bd))


## v0.5.0 (2026-11-02)

### Bug Fixes

- Update list_objects() to return all candidates regardless of object type
  ([`21cb0dd`](https://github.com/guillem-ps/policy-pattern/commit/21cb0ddf86e78966e629096913eda0be76478331))

- **changelog**: Restore automatic changelog generation and backfill missing entries
  ([`cb5408b`](https://github.com/guillem-ps/policy-pattern/commit/cb5408b265a5e26ae0dd48b987f6a89a84a4e1ce))

- **docs**: Clarify candidate_ids filtering in list_objects() documentation
  ([`60c8cc2`](https://github.com/guillem-ps/policy-pattern/commit/60c8cc2e74241e836ac40ec3c51e57663234dfa3))

- **docs**: Improve clarity and formatting in README.md
  ([`85179a5`](https://github.com/guillem-ps/policy-pattern/commit/85179a5acfb2dcc359f7af2d1a676fd2927a338a))

- **list_objects**: Close reverse-walk gaps
  ([`f441b87`](https://github.com/guillem-ps/policy-pattern/commit/f441b871d04bb6b0e7ea12fb06e528a58648d968))

### Chores

- Sync uv.lock and CITATION.cff date with released version
  ([`defcff9`](https://github.com/guillem-ps/policy-pattern/commit/defcff98d3f0042829652f1c51326aa5f7e03d59))

### Features

- Add list_objects() reverse lookup
  ([`9e5eb52`](https://github.com/guillem-ps/policy-pattern/commit/9e5eb52d3659a8fd597b85c3ed7589739420be3a))

- Add unit tests for reverse walk max depth and node limits in list_objects()
  ([`4d654f1`](https://github.com/guillem-ps/policy-pattern/commit/4d654f10c0cbfb5c8bd4b5d6450bb6a1af3df8cc))

- Enhance documentation for read_tuples_for_subject and related methods
  ([`b6929c0`](https://github.com/guillem-ps/policy-pattern/commit/b6929c0325d4c25a853550591876e23e9940845e))

- Update documentation for list_objects() reverse lookup and related semantics
  ([`1acadc9`](https://github.com/guillem-ps/policy-pattern/commit/1acadc9ad1d3dd44629162956b4ccd5ee822dabb))


## v0.4.1 (2026-10-31)

### Build System

- **deps**: Update dependencies of multiples components
  ([`690cc38`](https://github.com/guillem-ps/policy-pattern/commit/690cc38e74f74562eb09ea90403bc8cf4593b2c4))

### Chores

- Sync uv.lock and CITATION.cff date with released version
  ([`cfa2ee6`](https://github.com/guillem-ps/policy-pattern/commit/cfa2ee63336e241cc8a213d4d6da2e27e2dbe16e))

### Documentation

- Add CODE_STYLE.md and TESTING.md, remove stale conventions
  ([`25bf9ee`](https://github.com/guillem-ps/policy-pattern/commit/25bf9eea9a5a76655cdd301524f2ad1fc939b083))

- Update .gitignore to include additional skills/plugins directories
  ([`2322294`](https://github.com/guillem-ps/policy-pattern/commit/232229406497a2313ac2e4184d5ea01f190a2222))

### Testing

- Add test for permissions dict mutation in Type class
  ([`bb350bf`](https://github.com/guillem-ps/policy-pattern/commit/bb350bf96469acaa3dfab45984b25e451cd03eae))


## v0.4.0 (2026-10-29)

### Chores

- Sync uv.lock and CITATION.cff date with released version
  ([`44f6484`](https://github.com/guillem-ps/policy-pattern/commit/44f6484015155db8393f785a4db647b7cb7d09ff))

### Features

- **evaluator**: Add check_many() for batch processing of authorization requests
  ([`7c680fe`](https://github.com/guillem-ps/policy-pattern/commit/7c680feacb88aea4a9892c3c12511b4aca5ff7f2))

- **evaluator**: Update EvaluationBudget to clarify resource limits for check_many() calls
  ([`b00f3cd`](https://github.com/guillem-ps/policy-pattern/commit/b00f3cdfd2bd5beda7a6744545ad453297f30b11))

- **tests**: Add tests for check_many() max_depth behavior in evaluator
  ([`fe7b31a`](https://github.com/guillem-ps/policy-pattern/commit/fe7b31adfccb0b5936cc2e8ac789fc4ef77c2877))

- **tests**: Add test for memoization in check_many() with shared requests
  ([`5ad60fc`](https://github.com/guillem-ps/policy-pattern/commit/5ad60fc1fdc4a04aeb47ffb302e08ff37ab4c3f3))

- **tests**: Add read counting store and view for tracking read operations
  ([`adedc44`](https://github.com/guillem-ps/policy-pattern/commit/adedc448ed68c4acd4cbd9e27ebc0fb1c02aadd7))

### Refactoring

- **postgres**: Rename tests file for more context in filename
  ([`ca5d52f`](https://github.com/guillem-ps/policy-pattern/commit/ca5d52f5184456faaf6a4064694265706598db89))

- **tests**: Deduplicate and reorder test helpers
  ([`104b4ed`](https://github.com/guillem-ps/policy-pattern/commit/104b4eddd0299177e4554dbcf28e40f7ba31c795))

- **tests**: Remove unused _chain_of_groups function and replace its usage with _chain function
  ([`6b1d830`](https://github.com/guillem-ps/policy-pattern/commit/6b1d8302d16ac267c588e9c204f05949337bf2d6))


## v0.3.0 (2026-10-18)

### Bug Fixes

- **imports**: Update import paths for InvalidIdentifierError in models
  ([`e92a417`](https://github.com/guillem-ps/policy-pattern/commit/e92a4179ae91c403cd1af7f8e11e1d3091098ecc))

- **tests**: Suppress pyright warnings for private usage in permission checks
  ([`b203f60`](https://github.com/guillem-ps/policy-pattern/commit/b203f6032621ccba25fabaa694f7b9de2b2c06c5))

- **tests**: Update unit test marker description for clarity
  ([`da01615`](https://github.com/guillem-ps/policy-pattern/commit/da0161570ae4ba7c6b3cf9e5d88bc7ba4e8e5559))

### Chores

- Sync uv.lock and CITATION.cff date with released version
  ([`e308a34`](https://github.com/guillem-ps/policy-pattern/commit/e308a34881c35dd909758abf824100e500bf706d))

### Continuous Integration

- **lint**: Optimize linting and testing commands
  ([`6d44acb`](https://github.com/guillem-ps/policy-pattern/commit/6d44acb090190257ded8f5b2fdefb9b6a7c19156))

- **tests**: Add PostgreSQL integration tests to CI pipeline
  ([`c0586bc`](https://github.com/guillem-ps/policy-pattern/commit/c0586bc8c1b4de0a4633d0668d1564930deaa29c))

### Documentation

- Clarify architecture conventions for storage backend integration
  ([`be19d7e`](https://github.com/guillem-ps/policy-pattern/commit/be19d7ed18cab23e6d5ff8d5e3ffea98ca524334))

### Features

- **dependencies**: Add psycopg and psycopg-pool for PostgreSQL support
  ([`ef1edc7`](https://github.com/guillem-ps/policy-pattern/commit/ef1edc7505b15f073062140b848f6a375405df56))

- **postgres**: Implement PostgreSQL TupleStore adapter and related functionality
  ([`c255ad9`](https://github.com/guillem-ps/policy-pattern/commit/c255ad997b2de0b7886c7a845438ed62df1fbbc4))

- **postgres**: Add auto_create_schema option for PostgresTupleStore and update documentation
  ([`260d9fd`](https://github.com/guillem-ps/policy-pattern/commit/260d9fdbe7d8c82b080d7e7bc85a8bd0d8066690))

- **postgres**: Implement IndexEntryTooLargeError for oversized index entries in PostgresTupleStore
  ([`1feb43b`](https://github.com/guillem-ps/policy-pattern/commit/1feb43b59f4ac541418910dbc557f354a4b60a29))

- **tests**: Add integration test for migrated PostgreSQL table schema
  ([`e4a5594`](https://github.com/guillem-ps/policy-pattern/commit/e4a5594f1b677c6f3ad28861d3c472813d7906e8))

- **tests**: Add PostgreSQL integration tests and fixtures for TupleStore
  ([`fd885c7`](https://github.com/guillem-ps/policy-pattern/commit/fd885c772ef9f3ace6b2c3c76ea310e48301d129))

- **tests**: Add pytest-randomly for shuffling test execution order
  ([`16966b0`](https://github.com/guillem-ps/policy-pattern/commit/16966b086f0329adce2255c0477626fc67f03c60))

### Refactoring

- **adapters**: Remove unused imports from __init__.py
  ([`61b8c77`](https://github.com/guillem-ps/policy-pattern/commit/61b8c7703c4227ba5ecd0ae0fa793de0018f81d9))

- **tests**: Rename PostgreSQL integration test job for clarity
  ([`1956bc2`](https://github.com/guillem-ps/policy-pattern/commit/1956bc21287944c6e26c230d186de0edbc976a83))

### Testing

- **marks**: Tag pytest markers per test instead of module-wide pytestmark
  ([`5dbceed`](https://github.com/guillem-ps/policy-pattern/commit/5dbceede3a7b3d39d37b7748e8b1a64dd77d62f7))


## v0.2.5 (2026-10-04)

### Bug Fixes

- **docs**: Update README example to include complete model setup and usage
  ([`7d03852`](https://github.com/guillem-ps/policy-pattern/commit/7d038523b2d283fc3257c55a42c46d39d2a7b869))

### Chores

- Sync uv.lock and CITATION.cff date with released version
  ([`adbda5a`](https://github.com/guillem-ps/policy-pattern/commit/adbda5a3f04e0814288080d60eda8ff626fda8bc))


## v0.2.4 (2026-10-04)

### Bug Fixes

- **format**: Solve type checking for TupleStore and View instantiation in tests
  ([`fb9f428`](https://github.com/guillem-ps/policy-pattern/commit/fb9f4285271c3d408b2ff04bc0321ef610095466))

### Build System

- **deps**: Bump python-semantic-release/python-semantic-release
  ([`ee4ed35`](https://github.com/guillem-ps/policy-pattern/commit/ee4ed35ea865b6efac942e127b346719022f84b2))

- **deps**: Bump astral-sh/setup-uv
  ([`a1deea9`](https://github.com/guillem-ps/policy-pattern/commit/a1deea92ae4efa146c53527635b4fad1907df26b))

- **deps**: Bump the codeql-action group across 1 directory with 2 updates
  ([`523584d`](https://github.com/guillem-ps/policy-pattern/commit/523584ddf017717b6ed6cd5aa31f96206e7d5fb7))

- **deps-dev**: Update uv-build requirement
  ([`7188013`](https://github.com/guillem-ps/policy-pattern/commit/7188013992d4b0640d46b471aff6ce98fb8955b8))

- **deps-dev**: Bump ruff from 0.16.7 to 0.16.9
  ([`9653c54`](https://github.com/guillem-ps/policy-pattern/commit/9653c54c68b99feb035f871796907a05a688dfcb))

- **deps-dev**: Bump ty from 0.0.80 to 0.0.84
  ([`7ad35b5`](https://github.com/guillem-ps/policy-pattern/commit/7ad35b5b233ffcd7987a8f851f190537f769dd9c))

### Chores

- Sync uv.lock and CITATION.cff date with released version
  ([`bb4393e`](https://github.com/guillem-ps/policy-pattern/commit/bb4393e9d91f571e6161cfd10d7a18768499372f))


## v0.2.3 (2026-10-03)

### Build System

- **release**: Auto-sync CITATION.cff version on every release
  ([`1b71f24`](https://github.com/guillem-ps/policy-pattern/commit/1b71f24d1d6e81057d68d16d2778f65629292039))

Added it manually in the previous commit alongside the SECURITY.md fix, but hand-editing it means it
  goes stale again the next release — same class of bug this PR exists to fix.

version_variables regex-replaces CITATION.cff's `version:` line on every semantic-release run, same
  mechanism as version_toml for pyproject.toml. Verified against the installed engine directly: it
  matches `version: x.y.z` but correctly skips `cff-version: 1.2.0` (negative lookbehind excludes
  the hyphen-prefixed variant).

date-released isn't covered by version_variables (version-string only) — stays manually maintained
  for now.

- **release**: Stamp CITATION.cff's date-released on every release
  ([`4a51120`](https://github.com/guillem-ps/policy-pattern/commit/4a51120498a7f0785fe1ae5bed1b85f2fd806b86))

version_variables only touches the `version:` field — it matches a semver pattern, date-released
  isn't one, so it would've gone stale again on the very next release regardless of how often they
  happen.

Extended the existing uv.lock sync step to also sed-replace date-released with the current UTC date
  and bundle both files into the same post-release commit.

### Chores

- Sync uv.lock with released version
  ([`3fff949`](https://github.com/guillem-ps/policy-pattern/commit/3fff94928de0c6fc3577693c891c354d24ca6859))

### Documentation

- Clarify project status in SECURITY.md
  ([`5269223`](https://github.com/guillem-ps/policy-pattern/commit/52692237e0edd89c51dc680510435654f9c59afa))

- Fix stale pre-release claims in SECURITY.md and CITATION.cff
  ([`6685b6b`](https://github.com/guillem-ps/policy-pattern/commit/6685b6bfa38118050818c4d036f3c556cac28775))

Both files were written before the first release and still said so — SECURITY.md claimed "no
  released package and no deployed consumer yet", CITATION.cff omitted version/date-released "not
  released yet". Neither is true anymore: policy-pattern is on PyPI at 0.2.2.

Updated SECURITY.md's project status and supported-versions sections to reflect an actual pre-1.0
  release policy, and added version/date-released/repository-artifact to CITATION.cff.


## v0.2.2 (2026-10-03)

### Chores

- Sync uv.lock with released version
  ([`b693fde`](https://github.com/guillem-ps/policy-pattern/commit/b693fde9fc33cfeb9bafa54555a11f7c67844232))


## v0.2.1 (2026-10-03)

### Bug Fixes

- **.gitignore**: Add requirements files and notes directory to exclusion list
  ([`5216028`](https://github.com/guillem-ps/policy-pattern/commit/52160288fd0dfc61b3ac756daa69653ea2facb2e))

- **dependabot**: Untrack requirements exports so uv.lock updates work
  ([`003b60d`](https://github.com/guillem-ps/policy-pattern/commit/003b60dae87c66ac38fab3812cbd56e67bfa9041))

- **docs**: Update version badge link in README.md
  ([`d534d66`](https://github.com/guillem-ps/policy-pattern/commit/d534d66bfa3c72399256e939a9713f3ce5aeadef))

- **release**: Restore .git ownership before syncing uv.lock, resync to 0.2.0
  ([`5021509`](https://github.com/guillem-ps/policy-pattern/commit/50215090f919b40c0a5d04ca6d75c3496eded09f))

semantic-release's Docker container runs as root and commits/tags there, leaving .git owned by root.
  The next step (git commit for uv.lock) then fails: "fatal: could not open '.git/COMMIT_EDITMSG':
  Permission denied". Chown .git back to the runner user first.

Also resyncs uv.lock to the already-released 0.2.0 to unblock CI now.

### Continuous Integration

- **dependabot**: Group codeql-action updates, drop the useless uv ecosystem
  ([`baa761b`](https://github.com/guillem-ps/policy-pattern/commit/baa761b2b406e57b5fb9bd8b17f48a3a44d97fa4))


## v0.2.0 (2026-10-02)

### Bug Fixes

- **release**: Sync uv.lock to 0.1.2, remove dead build_command
  ([`75d5229`](https://github.com/guillem-ps/policy-pattern/commit/75d5229fe099f628519692e37f5360fb0087f377))

build_command ran (confirmed in CI logs: "Updated policy-pattern v0.1.1 -> v0.1.2") but
  semantic-release never stages its output into its own commit — only version_toml-listed files get
  committed. The line was a no-op; removed. The release.yaml sync step added in 52c7561 is what
  actually fixes this going forward.

### Features

- **release**: Add step to sync uv.lock with released version
  ([`52c7561`](https://github.com/guillem-ps/policy-pattern/commit/52c75612402ede63db508cd245a0432e0a40c9b5))


## v0.1.2 (2026-10-02)

### Bug Fixes

- **release**: Remove uv.lock sync step from release pipeline and add build command to
  pyproject.toml
  ([`5cc681b`](https://github.com/guillem-ps/policy-pattern/commit/5cc681bb22fa940b4dc6a34e3d7ad5376d191934))

- **release**: Sync uv.lock with released version and auto-sync on future releases
  ([`e1d8b6d`](https://github.com/guillem-ps/policy-pattern/commit/e1d8b6d05e7d2101d9210aa49dc0dd11b6b202c9))

### Build System

- **deps**: Batch GitHub Actions dependency bumps
  ([`eaf1964`](https://github.com/guillem-ps/policy-pattern/commit/eaf1964befce43d733c94da16cacdf60cf48550b))

Combines 4 dependabot PRs into one merge to avoid 4 separate semantic-release patch bumps for what's
  the same kind of change:

- github/codeql-action/init, analyze: v3 -> v3.38.2 (#10, #13) - codecov/codecov-action: v4.6.0 ->
  v7.1.1 (#3) - python-semantic-release/python-semantic-release: v9 -> v9.21.2 (#14)

All SHA-pinned per the repo's Actions security policy; comments updated to match. No breaking input
  changes for how this repo uses any of the three actions (verified: codecov's files/token/
  fail_ci_if_error inputs unchanged; checkout already at v7 separately via #12; codeql-action and
  python-semantic-release are patch bumps within the same major).


## v0.1.1 (2026-10-02)

### Build System

- **deps**: Bump actions/checkout from 4.4.0 to 7.0.1
  ([`d72cc3b`](https://github.com/guillem-ps/policy-pattern/commit/d72cc3b92b6769d8a670168d094474e20a5ce73e))

Bumps [actions/checkout](https://github.com/actions/checkout) from 4.4.0 to 7.0.1. - [Release
  notes](https://github.com/actions/checkout/releases) -
  [Changelog](https://github.com/actions/checkout/blob/main/CHANGELOG.md) -
  [Commits](https://github.com/actions/checkout/compare/11d5960a326750d5838078e36cf38b85af677262...3d3c42e5aac5ba805825da76410c181273ba90b1)

--- updated-dependencies: - dependency-name: actions/checkout dependency-version: 7.0.1

dependency-type: direct:production

update-type: version-update:semver-major ...

Signed-off-by: dependabot[bot] <support@github.com>


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
