# palewi.re Makefile

export UV_NO_ENV_FILE = 1

.PHONY: help bootstrap ci-bootstrap install hooks serve check test lint typecheck django-check fmt

help:
	@echo "Available targets:"
	@echo "  bootstrap  Prepare dependencies and hooks"
	@echo "  ci-bootstrap  Prepare dependencies for CI"
	@echo "  install    Install all dependencies without changing Git hooks"
	@echo "  hooks      Install pre-commit hooks"
	@echo "  serve      Start the development server"
	@echo "  check      Run the same lint, type, Django, and test checks as CI"
	@echo "  test       Run tests only"
	@echo "  lint       Run Ruff linter and format check"
	@echo "  typecheck  Run ty static type analysis"
	@echo "  fmt        Auto-format with Ruff"

install:
	uv sync --locked --group dev

hooks:
	uv run pre-commit install

bootstrap: install hooks

ci-bootstrap: install

serve:
	uv run python -m scripts.worktree serve

check: lint typecheck django-check test

test:
	uv run pytest tests/

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run ty check --exit-zero-on-warning .

django-check:
	uv run python manage.py check

fmt:
	uv run ruff check --fix .
	uv run ruff format .
