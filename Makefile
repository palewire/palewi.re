# palewi.re Makefile

export UV_NO_ENV_FILE = 1

.PHONY: help install serve check test lint typecheck fmt migrate

help:
	@echo "Available targets:"
	@echo "  install    Install all dependencies (requires uv)"
	@echo "  serve      Start the development server"
	@echo "  check      Run the full quality gate (lint + typecheck + tests)"
	@echo "  test       Run tests only"
	@echo "  lint       Run Ruff linter and format check"
	@echo "  typecheck  Run ty static type analysis"
	@echo "  fmt        Auto-format with Ruff"
	@echo "  migrate    Apply database migrations"

install:
	uv sync --group dev
	uv run pre-commit install

serve:
	uv run python manage.py runserver

check: lint typecheck
	uv run pytest tests/

test:
	uv run pytest tests/

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run ty check --exit-zero-on-warning .

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
