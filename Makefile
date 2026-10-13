PYTHON_VERSIONS := 3.12 3.13 3.14

.PHONY: test test-all coverage lint format

test: # Run tests on the default interpreter
	uv run pytest

test-all: # Run tests on every supported Python version, always cleaning up the per-version venvs afterward
	@trap 'rm -rf $(foreach v,$(PYTHON_VERSIONS),.venv$(v))' 0; \
	for v in $(PYTHON_VERSIONS); do \
		echo "--- Python $$v ---"; \
		UV_PROJECT_ENVIRONMENT=.venv$$v env -u VIRTUAL_ENV uv run --python $$v pytest || exit 1; \
	done

coverage: # Run tests with coverage report, preserving the real pass/fail status
	@uv run coverage run -m pytest; status=$$?; \
	uv run coverage combine; \
	uv run coverage report || status=$$?; \
	uv run coverage erase; \
	exit $$status

lint: # Type-check (library source only, no PostgreSQL drivers needed) and lint
	uv run ty check policy_pattern
	uv run ruff check

format: # Format code
	uv run ruff format
