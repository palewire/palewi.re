# Copilot Instructions for palewi.re

## Project overview

This is a Django 5.2 personal site for Ben Welsh. The main apps are:

- `coltrane/` — blog posts, clips, talks, docs, bots, and ticker (personal publishing)
- `bona_fides/` — bio page data (awards, skills, talks, docs, clips)
- `toolbox/` — shared utilities (context processors, middleware, health check)
- `project/` — settings and URL routing

## Setup

```bash
uv sync --group dev
createdb palewire
uv run python manage.py migrate
```

## Quality gate

Always run before committing:

```bash
make check
```

This runs Ruff lint + format check, **ty static type analysis**, and pytest with coverage.

## Key conventions

- **Packaging**: `uv` + `pyproject.toml` + `uv.lock`. Never use `pip install` directly.
- **Linting**: Ruff with `select = ["E", "F", "W", "I", "UP"]` (UP031 ignored).
- **Type checking**: `ty check .` — Django dynamic attributes are downgraded to warnings; new code should pass clean.
- **Tests**: pytest-django in `tests/`. Requires PostgreSQL.
- **Settings**: `PRODUCTION=true` enables full security hardening. `SECRET_KEY` must be set in production.
- **Static files**: Served by WhiteNoise from `collected_static/`. Run `python manage.py collectstatic` before Heroku deploys.
- **Database**: dj-database-url parses `DATABASE_URL`. Default local: `postgres://postgres@localhost/palewire`.
- **django-heroku is removed**: Database, WhiteNoise, and security are configured explicitly in `project/settings.py`.

## Deployment

- Deploys to Heroku from `main` after CI passes.
- `Procfile` runs `python manage.py migrate --noinput` as the release step.
- `/health/` endpoint verifies DB connectivity.
- For rollback: `heroku rollback vN`.

## Post-deployment smoke checks

The `.github/workflows/smoke.yaml` workflow verifies health, bio page, and root redirect.
Run it manually via **Actions → Smoke test → Run workflow**, or trigger it automatically by
configuring Heroku's Deploy Hook to send a `repository_dispatch` event.

## Branch protection

`main` is protected by a GitHub ruleset (Protect main) that requires the **Lint** and **Test**
CI jobs to pass before merging. Repository admins can bypass in emergencies.

## Adding tests

Place test files under `tests/`. Use `@pytest.mark.django_db` for database tests. Coverage floor is 40%.

## Content

YAML content files live in `coltrane/content/`. Bio markdown is at `coltrane/content/bio.md`.
