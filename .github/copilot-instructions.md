# Copilot Instructions for palewi.re

## Project overview

This is a Django 5.2 personal site for Ben Welsh. The main apps are:

- `coltrane/` — blog posts, clips, talks, docs, bots, and ticker (personal publishing)
- `bona_fides/` — bio page data (awards, skills, talks, docs, clips)
- `toolbox/` — shared utilities (context processors and health check)
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

## Releases

Apply exactly one changelog category to every pull request: `feature`,
`improvement`, `fix`, `maintenance`, or `skip-changelog`. The required Lint
check enforces this. `enhancement` counts as an improvement; Dependabot's
`dependencies` and `github_actions` labels count as maintenance. Read
`RELEASING.md` before creating a release. GitHub Releases are the site's
public changelog. Use semantic versions, create a draft from the deployed
`main` commit, and publish only after the production smoke test passes.

## Key conventions

- **Packaging**: `uv` + `pyproject.toml` + `uv.lock`. Never use `pip install` directly.
- **Bootstrap**: use `make bootstrap` in local worktrees and agent environments; it requires `uv`, Node.js, npm, and Wrangler. CI uses `make ci-bootstrap`.
- **Cloudflare access**: cloud-agent setup installs Wrangler 4.125.0 on fresh runners. Local bootstrap only checks for an existing CLI. Use `make cloudflare-check` for the non-destructive `wrangler whoami --json` check. Authenticate locally with `wrangler login` or a `CLOUDFLARE_API_TOKEN`; cloud agents require that token as a Copilot Agents secret with only User Details and Memberships read permissions. The vendored Wrangler skill's `@latest` installation advice does not apply here: agents must run `make check-wrangler` and use the existing pinned CLI. Do not configure or deploy DNS, zones, Pages, or Workers until a target is chosen.
- **Linting**: Ruff with `select = ["E", "F", "W", "I", "UP"]` (UP031 ignored).
- **Type checking**: `ty check .` — Django dynamic attributes are downgraded to warnings; new code should pass clean.
- **Tests**: pytest-django in `tests/`. No database service is required.
- **Static files**: Django collects a hashed manifest in `collected_static/` for local checks. The static-site Worker publishes the `dist/` build.
- **Database**: The public site is file-backed and has no runtime database configuration.
- **Clip archiving**: When adding or changing a URL in `coltrane/content/clips.yaml`, load the `archive-clips` skill, run `make archive-clips`, and retain the resulting `archive_url` or specific `archive_exemption`.

## Deployment

The `deploy-static-site` CI job builds Django's static site, deploys the
`workers/static-site` Worker, and deploys the validated legacy redirect route
plan after Lint and Test pass on `main`. It serves `palewi.re` and
`www.palewi.re`; the legacy redirect Worker serves the retired paths.

## Post-deployment smoke checks

Run the **Smoke test** workflow from Actions after a production deployment.

## Branch protection

`main` is protected by GitHub ruleset **"Protect main"** (id: 21237273) requiring the **Lint**
and **Test** CI jobs to pass before merge. Repository admins can bypass in emergencies.

## Adding tests

Place test files under `tests/`. Coverage floor is 40%.

## Content

YAML content files live in `coltrane/content/`. Bio markdown is at `coltrane/content/bio.md`.
