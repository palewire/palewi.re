# palewi.re Makefile

export UV_NO_ENV_FILE = 1

HOMEBREW_BIN := $(shell for path in /opt/homebrew/bin /usr/local/bin; do test -x "$$path/brew" && { printf '%s' "$$path"; break; }; done)
export PATH := $(HOME)/.local/bin:$(HOME)/.local/share/heroku/client/bin:$(HOMEBREW_BIN):$(PATH)

.PHONY: help bootstrap ci-bootstrap check-tools install hooks serve check test lint typecheck django-check fmt

help:
	@echo "Available targets:"
	@echo "  bootstrap  Check developer tools, then prepare dependencies and hooks"
	@echo "  ci-bootstrap  Prepare dependencies for CI"
	@echo "  check-tools  Confirm uv and the Heroku CLI are available"
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

check-tools:
	@command -v uv > /dev/null || { echo "uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/" >&2; exit 1; }
	@command -v heroku > /dev/null || { echo "The Heroku CLI is required. Install it from https://devcenter.heroku.com/articles/heroku-cli#install-the-heroku-cli" >&2; exit 1; }

bootstrap: check-tools install hooks

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
