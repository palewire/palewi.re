# Agent guide

## Start here

Run `make bootstrap` once after creating a clone or worktree. It installs locked
dependencies, prepares the local PostgreSQL database, applies migrations, and
installs the pre-commit hooks.

Run the development server with `make serve`. Linked worktrees automatically
receive an isolated database name and an available local port.

## Before finishing

Run `make check`. This is the same set of lint, type, Django, migration, and test
checks used by CI.

Keep changes focused. Add or update tests when behavior changes. Do not commit
secrets, generated files, local databases, or `.goals/` agent state.

## Project map

- `coltrane/`: publishing features and content
- `bona_fides/`: biography data
- `toolbox/`: shared utilities
- `project/`: Django settings and URL routing
- `tests/`: pytest suite

Use `uv` and `pyproject.toml` for Python dependencies, Ruff for formatting and
linting, and ty for static analysis.
