PYTHON_VERSIONS := 3.13 3.14

.PHONY: test test-all coverage lint format

test: # Run tests on the default interpreter
	uv run pytest

test-all: # Run tests on every supported Python version, always cleaning up the per-version venvs afterward
	@trap 'rm -rf $(foreach v,$(PYTHON_VERSIONS),.venv$(v))' EXIT; \
	for v in $(PYTHON_VERSIONS); do \
		echo "--- Python $$v ---"; \
		UV_PROJECT_ENVIRONMENT=.venv$$v env -u VIRTUAL_ENV uv run --python $$v pytest || exit 1; \
	done

coverage: # Run tests with coverage report
	uv run coverage run -m pytest; uv run coverage report; uv run coverage erase

lint: # Type-check and lint
	uv run ty check
	uv run ruff check

format: # Format code
	uv run ruff format
