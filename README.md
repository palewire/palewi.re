# palewi.re

Ben Welsh's personal site — a Django blog and portfolio at [palewi.re](https://palewi.re).

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/) for package management
- Node.js 24 for the pinned Dart Sass compiler
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) for local setup and Heroku commands
- [Wrangler 4.125.0](https://developers.cloudflare.com/workers/wrangler/install-and-update/) for Cloudflare account checks and the isolated Mastodon discovery Worker

## Setup

```bash
# Clone
git clone https://github.com/palewire/palewi.re.git
cd palewi.re

# Install dependencies and hooks
make bootstrap

# Start server
make serve
```

`make bootstrap` checks these commands before it installs anything. For its
commands, it also adds common user installation paths including
`$HOME/.local/bin`, Heroku's user client directory, npm's user directory,
Volta, asdf, fnm, and a detected Homebrew bin directory. It does not install
or authenticate any command.

The Sass compiler is an exact, locked npm dependency. `make serve` builds
expanded CSS with a source map. `make css` builds the compressed production
stylesheet used by CI and Heroku.

Install Wrangler once with:

```bash
npm install --global wrangler@4.125.0
```

Open the URL printed by the server. Linked Git worktrees automatically use
available local ports, so multiple agents can run the site at the same time.

## Environment variables

| Variable | Required in prod | Description |
|----------|-----------------|-------------|
| `SECRET_KEY` | Yes | Django secret key |
| `PRODUCTION` | No | Set `true` to enable production security |
| `DEBUG` | No | Set `false` to disable debug output |

## Quality gate

Run the complete quality gate before opening a pull request:

```bash
make check
```

This runs Ruff linting and formatting checks, ty static analysis, Django's
system check, and the full pytest suite. Coverage measures application and
maintenance source code (not tests) and must be at least 90%, raised from 40%.
CI uses the same Make targets.

To auto-format code:

```bash
make fmt
```

## Tests

```bash
make test
```

Tests and local serving do not require PostgreSQL or `DATABASE_URL`.

## Content catalogs

`coltrane/content/docs.yaml` lists the documentation catalog. Each record
requires `title`, `type`, and a unique `url`; `description` is optional.
`repository_url` is optional machine-readable metadata for a verified canonical
source repository. When set, it must be a unique HTTP(S) URL. It is not
displayed on the docs page.

## Blog post Markdown

Public posts in `coltrane/content/posts/` are one `.md` file each. Their YAML
front matter requires `title`, `slug`, and `published_at`; the datetime must
use the Los Angeles offset. `repr_image` and `wordpress_id` are optional.
Keep the body as raw HTML, including any `<pre lang="...">` code blocks. Do
not add drafts or a status field. The filename format is
`YYYY-MM-DD--slug.md`, and `posts-manifest.json` is the checked-in public
fingerprint generated during the production export.

To author a post, create a file with this shape:

```markdown
---
title: Example post
slug: example-post
published_at: "2026-08-24T09:00:00-07:00"
repr_image: "https://example.com/image.jpg" # optional
wordpress_id: 123 # optional legacy ID
---
<p>Write the published body as raw HTML.</p>
```

Only files in this directory are public. Drafts belong in a private workspace,
not this repository. Run `make serve`, open the printed local URL, and visit
`/posts/` or the post's date-based URL to preview it. Run `make check` before
committing to validate the front matter, public URL inventory, and rendering.

## Deployment

The app deploys to Heroku automatically when a pull request merges to `main` **after CI passes**.

Heroku must use the Node.js buildpack before the Python buildpack. The Node
build runs `npm run build:css`; the Python buildpack then runs `collectstatic`
and WhiteNoise creates the hashed stylesheet manifest.

The existing `palewire` app needs this one-time configuration before its first
deploy with this build:

```bash
heroku buildpacks:add --index 1 heroku/nodejs --app palewire
heroku config:unset DISABLE_COLLECTSTATIC --app palewire
```

The Heroku CLI is available in Copilot cloud-agent sessions through the
official installer in `.github/workflows/copilot-setup-steps.yml`. Authentication
is not part of repository setup. For a cloud agent that must run authenticated
Heroku commands, add `HEROKU_API_KEY` as a GitHub Copilot Agents secret; never
store it in this repository.

## Cloudflare access

Cloudflare access is limited to the non-destructive identity check:

```bash
make cloudflare-check
```

For local use, authenticate interactively with `wrangler login`, then run the
check. In non-interactive environments, set `CLOUDFLARE_API_TOKEN` in the
environment instead. Do not commit tokens or add them to `.env` files.

For a Copilot cloud-agent session, create a **user API token** with only
**User > User Details > Read** and **User > Memberships > Read**, then save it
as the `CLOUDFLARE_API_TOKEN` GitHub Copilot Agents secret. Restrict and expire
the token as your Cloudflare account allows. `wrangler whoami` does not need
`CLOUDFLARE_ACCOUNT_ID`, so do not add that secret or variable yet.

The cloud-agent setup installs the pinned Wrangler version on each fresh
runner. Local setup only finds an existing CLI. This repository does not
configure or deploy Cloudflare DNS, zones, Pages, or Workers until a maintainer
explicitly runs a deployment target.

### Mastodon discovery Worker

`workers/mastodon-well-known-proxy/` is an isolated, locked Node project for a
Cloudflare Worker. It supports only these production routes:

- `palewi.re/.well-known/webfinger`
- `palewi.re/.well-known/host-meta`
- `palewi.re/.well-known/nodeinfo`

All other traffic continues to the existing Heroku origin. The Worker accepts
only `GET` and `HEAD`, validates WebFinger resources for the `palewi.re`
domain, and proxies only to `https://mastodon.palewi.re` at the same approved
path. It does not follow upstream redirects. It uses a five-second upstream
timeout and a 1 MiB response limit, preserving safe caching and representation
headers. Responses include `X-Palewire-Discovery-Proxy: cloudflare-worker-v1`.
The Django routes and `django-proxy` dependency remain in place as the stage 1
fallback until the separate retirement PR.

Cloudflare route matching includes query strings, so the explicit attach command
uses a terminal `*` for each route to serve WebFinger requests with
`?resource=...`. The Worker still accepts only the three exact paths and returns
`404` for a suffix such as `webfinger-extra`; the wildcard cannot reach the
upstream unless that path check succeeds.

Run the isolated checks without contacting or changing Cloudflare:

```bash
make worker-test
make worker-validate
```

#### Stage 1 incident and safe retry

The first Stage 1 deploy on August 24, 2026 attached the routes before the
Worker was tested on Cloudflare. The Worker then returned `502` for every
matched route. The fixed Mastodon endpoints were healthy: WebFinger,
host-meta, and nodeinfo each returned `200` when contacted directly.

The Worker module exported the numeric `MAX_RESPONSE_BYTES` constant. Workerd
interprets module exports as Worker entries and only accepts functions or an
exported handler, so the module failed during startup before it made an
upstream request. The routes were removed by deleting that Worker, and Django
continues to serve all three endpoints. This has been reproduced with Wrangler
4.125.0 and local Miniflare. The regression test starts the bundled Worker in
workerd, which catches invalid module exports that direct TypeScript unit tests
miss.

The default Worker configuration intentionally has no production routes and
enables workers.dev and preview URLs. The canary deploy uses the separate
`palewire-mastodon-well-known-proxy-canary` Worker name, so it cannot update a
version currently serving production routes. A deployment must therefore follow
this canary-first sequence. Do not attach routes until the canary verification
has passed.

To deploy, authenticate with either local `wrangler login` OAuth or an API
token limited to the Cloudflare account and `palewi.re` zone that own these
routes. Automation needs **Account > Workers Scripts > Edit**, **Zone > Workers
Routes > Edit**, and **Zone > Zone > Read** for only the `palewi.re` zone. Save
it as the `CLOUDFLARE_API_TOKEN` Copilot Agents secret and save the owning
account ID as the `CLOUDFLARE_ACCOUNT_ID` secret. This deploy token is separate
from the read-only `whoami` token above; never reuse a broader token. The
account must already own the proxied `palewi.re` zone.

```bash
# 1. Build and test locally. This does not contact Cloudflare.
make worker-test
make worker-validate

# 2. Deploy a route-free canary. Wrangler prints a workers.dev or preview URL.
CONFIRM_WORKER_CANARY_DEPLOY=1 make worker-canary-deploy

# 3. Verify that exact canary URL before it can receive production traffic.
BASE_URL="https://the-url-printed-by-wrangler" make worker-verify-canary

# 4. Only after the canary passes, attach the three production routes.
CONFIRM_WORKER_ATTACH_ROUTES=1 make worker-attach-routes

# 5. Verify every live endpoint, expected content type, and Worker marker.
make worker-verify-production

# 6. Remove the separate canary Worker after the production check passes.
CONFIRM_WORKER_DELETE_CANARY=1 make worker-delete-canary
```

Both verification targets check valid requests for all three endpoints:

- WebFinger with `resource=acct:palewire@palewi.re` returns
  `application/jrd+json; charset=utf-8`.
- Host-meta returns `application/xrd+xml; charset=utf-8`.
- Nodeinfo returns `application/json; charset=utf-8`.

Each must return `200` and the exact
`X-Palewire-Discovery-Proxy: cloudflare-worker-v1` marker. The verifier is a
POSIX `/bin/sh` script and accepts `BASE_URL` for controlled local tests or a
canary. It prints a short endpoint-specific error and exits non-zero for a
timeout, unexpected status, content type, or marker.

If canary or production verification fails, do not retry route attachment.
Immediately return traffic to Django:

```bash
CONFIRM_WORKER_DETACH_ROUTES=1 make worker-detach-routes
```

This uses `wrangler delete --force`, which removes the Worker and its routes and
works with either Wrangler OAuth or `CLOUDFLARE_API_TOKEN`; it does not depend
on a separate API-only helper. Run the same operation explicitly for final
cleanup when needed:

```bash
CONFIRM_WORKER_DELETE=1 make worker-delete
```

Both commands are intentionally guarded. They are equivalent when routes are
still attached: Cloudflare cannot leave routes pointing at a deleted Worker.
They leave unrelated Workers and routes untouched.

For a normal production code rollback without route changes, use Cloudflare's
version controls after a verified canary. For a Stage 1 failure, detaching the
routes is safer because the retained Django fallback takes effect immediately.

The Stage 1 Worker does not change the Django fallback or begin Stage 2.

For the database retirement deployment, take a fresh Heroku backup first. Deploy
the exact merged SHA, then verify `/health/`, the main pages, all post
permalinks, feeds, sitemaps, and the smoke workflow. Only after that separate
review should the Heroku PostgreSQL add-on be considered for removal. Do not
remove it as part of the deploy.

GitHub releases summarize meaningful batches of deployed changes. See
[RELEASING.md](RELEASING.md) for the changelog and release process.

**Rollback** a bad deploy:

```bash
heroku releases
heroku rollback vN   # where N is the last good release number
```

## Health check

A lightweight health endpoint is available at `/health/`. It returns HTTP 200
and `{"status": "ok"}` when Django can serve requests.
