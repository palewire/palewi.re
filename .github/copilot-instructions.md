# Copilot Instructions for palewi.re

## Project overview

This is a Django 5.2 personal site for Ben Welsh. The main apps are:

- `coltrane/` — blog posts, clips, talks, docs, bots, and ticker (personal publishing)
- `bona_fides/` — bio page data (awards, skills, talks, docs, clips)
- `toolbox/` — shared utilities (context processors, middleware, health check)
- `project/` — settings and URL routing

## Setup

```bash
make bootstrap
```

Read `AGENTS.md` for the shared development workflow. Linked worktrees receive
an isolated PostgreSQL database and local server port automatically. Use
`make serve`; do not hard-code port 8000 or share another worktree's database.

## Quality gate

Always run before committing:

```bash
make check
```

This runs Ruff lint + format check, **ty static type analysis**, and pytest with coverage.

## Key conventions

- **Packaging**: `uv` + `pyproject.toml` + `uv.lock`. Never use `pip install` directly.
- **Bootstrap**: use `make bootstrap` in local worktrees, CI, and agent environments.
- **Linting**: Ruff with `select = ["E", "F", "W", "I", "UP"]` (UP031 ignored).
- **Type checking**: `ty check .` — Django dynamic attributes are downgraded to warnings; new code should pass clean.
- **Tests**: pytest-django in `tests/`. Requires PostgreSQL.
- **Settings**: `PRODUCTION=true` enables full security hardening. `SECRET_KEY` must be set in production.
- **Static files**: Served by WhiteNoise from `collected_static/`. Run `python manage.py collectstatic` before Heroku deploys.
- **Database**: dj-database-url parses `DATABASE_URL`. Default local: `postgres://postgres@localhost/palewire`.
- **django-heroku is removed**: Database, WhiteNoise, and security are configured explicitly in `project/settings.py`.

## Deployment

- The `palewire` app is the **production** stage of the **palewire** Heroku pipeline.
- The pipeline is connected to `palewire/palewi.re` on GitHub.
- To enable **auto-deploy from `main` after CI passes**, open the pipeline in the Heroku Dashboard
  → Production → "Enable Automatic Deploys" → branch `main` → tick "Wait for CI to pass before deploy".
- `Procfile` runs `python manage.py migrate --noinput` as the release step.
- `/health/` endpoint verifies DB connectivity.
- Rollback: `heroku releases --app palewire` then `heroku rollback vN --app palewire`.
- Stack: heroku-24 (Cedar). Buildpacks: `heroku/python` + `heroku-buildpack-django-sass`.

## Review Apps

Review Apps are **manually created** (no auto-create on PR). To create one:
1. Open the [palewire pipeline](https://dashboard.heroku.com/pipelines/de4cf89d-89a1-444d-813e-506da286d905).
2. Click **Open app** next to the pull request under Review Apps.

## Post-deployment smoke checks

`.github/workflows/smoke.yaml` fires automatically after Heroku reports a successful deployment,
or run it manually via **Actions → Smoke test → Run workflow**.
No Heroku API token is required.

## Branch protection

`main` is protected by GitHub ruleset **"Protect main"** (id: 21237273) requiring the **Lint**
and **Test** CI jobs to pass before merge. Repository admins can bypass in emergencies.

## Adding tests

Place test files under `tests/`. Use `@pytest.mark.django_db` for database tests. Coverage floor is 40%.

## Content

YAML content files live in `coltrane/content/`. Bio markdown is at `coltrane/content/bio.md`.
