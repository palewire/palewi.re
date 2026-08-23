# palewi.re Makefile

export UV_NO_ENV_FILE = 1

.PHONY: help bootstrap install serve check test lint typecheck django-check migrations-check fmt migrate

help:
	@echo "Available targets:"
	@echo "  bootstrap  Prepare dependencies, database, migrations, and hooks"
	@echo "  install    Install all dependencies (requires uv)"
	@echo "  serve      Start the development server"
	@echo "  check      Run the same lint, type, Django, migration, and test checks as CI"
	@echo "  test       Run tests only"
	@echo "  lint       Run Ruff linter and format check"
	@echo "  typecheck  Run ty static type analysis"
	@echo "  fmt        Auto-format with Ruff"
	@echo "  migrate    Apply database migrations"

install:
	uv sync --locked --group dev
	uv run pre-commit install

bootstrap: install
	uv run python -m scripts.worktree create-database
	uv run python manage.py migrate

serve:
	uv run python -m scripts.worktree serve

check: lint typecheck migrations-check django-check test

test:
	uv run pytest tests/

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run ty check --exit-zero-on-warning .

django-check:
	uv run python manage.py check

migrations-check:
	uv run python manage.py makemigrations --check --dry-run

fmt:
	uv run ruff check --fix .
	uv run ruff format .

migrate:
	uv run python manage.py migrate

backupdb:
	heroku pg:backups:capture

downloaddb:
	heroku pg:backups:download

restoredb:
	pg_restore --verbose --clean --no-acl --no-owner -h localhost -U postgres -d palewire latest.dump

loaddb: backupdb downloaddb restoredb
	rm latest.dump
