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
an available local server port automatically. Use `make serve`; do not hard-code
port 8000.

## Quality gate

Always run before committing:

```bash
make check
```

This runs Ruff lint + format check, **ty static type analysis**, and pytest with coverage.

## Key conventions

- **Packaging**: `uv` + `pyproject.toml` + `uv.lock`. Never use `pip install` directly.
- **Bootstrap**: use `make bootstrap` in local worktrees and agent environments; it requires `uv`, the Heroku CLI, and Wrangler. CI uses `make ci-bootstrap`.
- **Cloud Heroku access**: setup installs the CLI but does not authenticate. If an agent needs Heroku access, use a `HEROKU_API_KEY` GitHub Copilot Agents secret; never commit credentials or auth files.
- **Cloudflare access**: cloud-agent setup installs Wrangler 4.125.0 on fresh runners. Local bootstrap only checks for an existing CLI. Use `make cloudflare-check` for the non-destructive `wrangler whoami --json` check. Authenticate locally with `wrangler login` or a `CLOUDFLARE_API_TOKEN`; cloud agents require that token as a Copilot Agents secret with only User Details and Memberships read permissions. The vendored Wrangler skill's `@latest` installation advice does not apply here: agents must run `make check-wrangler` and use the existing pinned CLI. Do not configure or deploy DNS, zones, Pages, or Workers until a target is chosen.
- **Linting**: Ruff with `select = ["E", "F", "W", "I", "UP"]` (UP031 ignored).
- **Type checking**: `ty check .` — Django dynamic attributes are downgraded to warnings; new code should pass clean.
- **Tests**: pytest-django in `tests/`. No database service is required.
- **Settings**: `PRODUCTION=true` enables full security hardening. `SECRET_KEY` must be set in production.
- **Static files**: Served by WhiteNoise from `collected_static/`. Run `python manage.py collectstatic` before Heroku deploys.
- **Database**: The public site is file-backed and has no runtime database configuration.

## Deployment

- The `palewire` app is the **production** stage of the **palewire** Heroku pipeline.
- The pipeline is connected to `palewire/palewi.re` on GitHub.
- To enable **auto-deploy from `main` after CI passes**, open the pipeline in the Heroku Dashboard
  → Production → "Enable Automatic Deploys" → branch `main` → tick "Wait for CI to pass before deploy".
- `/health/` confirms that Django can serve requests.
- Rollback: `heroku releases --app palewire` then `heroku rollback vN --app palewire`.
- Stack: heroku-24 (Cedar). Buildpack: `heroku/python`.
- Production sets `SECURE_SSL_REDIRECT=false` because Cloudflare terminates TLS
  before connecting to the Heroku origin; Cloudflare remains responsible for
  redirecting public HTTP traffic to HTTPS.

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

Place test files under `tests/`. Coverage floor is 40%.

## Content

YAML content files live in `coltrane/content/`. Bio markdown is at `coltrane/content/bio.md`.
