# palewi.re

Ben Welsh's personal site — a Django blog and portfolio at [palewi.re](https://palewi.re).

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/) for package management
- Node.js 24 for the pinned Dart Sass compiler
- [Wrangler 4.125.0](https://developers.cloudflare.com/workers/wrangler/install-and-update/) for Cloudflare account checks and the isolated Workers

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
`$HOME/.local/bin`, npm's user directory, Volta, asdf, fnm, and a detected
Homebrew bin directory. It does not install or authenticate any command.

The Sass compiler is an exact, locked npm dependency. `make serve` builds
expanded CSS with a source map. `make css` builds the compressed production
stylesheet used by CI and the static-site Worker build.

Install Wrangler once with:

```bash
npm install --global wrangler@4.125.0
```

Open the URL printed by the server. Linked Git worktrees automatically use
available local ports, so multiple agents can run the site at the same time.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | No | Django secret key for local development and checks |
| `DEBUG` | No | Set `false` to disable debug output |
| `SAVEPAGENOW_ACCESS_KEY` | No | Internet Archive access key used by `make archive-clips` |
| `SAVEPAGENOW_SECRET_KEY` | No | Internet Archive secret key used by `make archive-clips` |
| `MEDIA_ARCHIVE_PATH` | No | Directory outside the repo where `make media-archive-backup`/`verify` store media and the manifest |
| `R2_ACCOUNT_ID` | No | Cloudflare account ID used only by the manual private R2 media replica |
| `R2_ACCESS_KEY_ID` | No | Bucket-scoped R2 S3 access key, supplied outside Git |
| `R2_SECRET_ACCESS_KEY` | No | Bucket-scoped R2 S3 secret, supplied outside Git |
| `MEDIA_ARCHIVE_R2_BUCKET` | No | Private R2 bucket name; defaults to `palewire-media-archive` |

## Quality gate

Run the complete quality gate before opening a pull request:

```bash
make check
```

This runs Ruff linting and formatting checks, ty static analysis, Django's
system check, and the full pytest suite. Coverage measures application and
maintenance source code (not tests) and must be at least 90%, raised from 40%.
The required CI Test job also runs both locked Worker test targets and both
Worker validation targets.

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

`coltrane/content/clips.yaml` stores a Wayback snapshot alongside each clip
URL. After adding or changing a clip, run:

```bash
make archive-clips
make check-clip-archives
```

The first command reuses an existing snapshot or creates one with the
`SAVEPAGENOW_ACCESS_KEY` and `SAVEPAGENOW_SECRET_KEY` environment variables.
It writes progress after every clip and supports resumable batches with
`uv run python -m scripts.archive_clips archive --limit 10`.

## Media archive (audio/video backup)

`scripts/media_archive/` finds every playable audio/video source referenced
by `coltrane/content/talks.yaml` and blog posts, then uses `yt-dlp` to save a
durable copy to a directory of your choosing, entirely **outside** this
repository (see issue #176). Read
[`.github/skills/archive-media/SKILL.md`](.github/skills/archive-media/SKILL.md)
for the full workflow. In short:

```bash
# 1. See what would be backed up. Network-free, no archive root needed.
make media-archive-inventory

# 2. Download pending media to your chosen external directory.
ARCHIVE_ROOT=/absolute/path/outside/the/repo make media-archive-backup

# 3. Offline checksum audit of what's already archived.
uv run python -m scripts.media_archive verify --archive-root /absolute/path/outside/the/repo
```

`--archive-root` (or the `MEDIA_ARCHIVE_PATH` environment variable) must
point outside this repository; the command refuses paths inside it. Runs are
idempotent and resumable, and a JSON manifest inside the archive root tracks
every source URL, checksum, size, and any failure so nothing is silently
dropped. `ffmpeg` is only needed for sources that require it (YouTube, Vimeo)
and is never installed automatically by `make bootstrap`.

### Private R2 replica

The local archive remains the source of truth. A private R2 bucket is a manual,
offsite replica only: it has no public domain, Worker binding, CORS policy, or
scheduled sync. See [the R2 archive runbook](docs/media-archive-r2.md) for
bucket-scoped credentials, sync, remote verification, selected-file recovery,
and cost-aware maintenance.

## Blog post authoring

Public posts in `coltrane/content/posts/` are one `.md` file each. Git and a
merged pull request are the publishing workflow; do not add drafts or a status
field to this repository.

1. Create the post from its title and Los Angeles publication time. The command
   prompts directly for both values, so punctuation and dollar signs in titles
   are preserved. Supply the offset that applies at that local time (`-08:00`
   in standard time, `-07:00` in daylight time).

   ```bash
   make new-post
   ```

   The command creates `YYYY-MM-DD--slug.md`, generates the required front
   matter, checks for existing files, duplicate slugs, and duplicate public
   URLs, then prints the new path. It never overwrites a post. It rejects an
   invalid date, missing offset, or a time that is not valid in Los Angeles.
   For a scripted command, pass the values directly with shell-safe quoting:

   ```bash
   uv run python -m scripts.new_post --title 'Example post: $5' --published-at '2026-08-24T09:00:00-07:00'
   ```

2. Edit the new file. Keep the body as raw HTML, including any
   `<pre lang="...">` code blocks. The command's placeholder is deliberately
   raw HTML. `repr_image` and `wordpress_id` are optional legacy fields.

3. Validate and preview the post locally.

   ```bash
   make check
   make serve
   # Open the printed URL, then visit /posts/ or the new post URL.
   make bake
   ```

4. Commit the new Markdown file, push the branch, and open a pull request.
   Merging that pull request to `main` publishes the post.

Only files in this directory are public. Drafts belong in a private workspace,
not this repository. `posts-manifest.json` is the checked-in public fingerprint
from the historical export; do not edit it for new posts.

## Deployment

Merges to `main` run the `deploy-static-site` CI job after Lint and Test pass.
It builds Django's static output in `dist/` and deploys
`workers/static-site`, which serves `palewi.re` and `www.palewi.re`.
Django is a build-time publishing system; it does not serve the public site.

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

The static-site Worker serves all other public paths. The Worker accepts
only `GET` and `HEAD`, validates WebFinger resources for the `palewi.re`
domain, and proxies only to `https://mastodon.palewi.re` at the same approved
path. It does not follow upstream redirects. It uses a five-second upstream
timeout and a 1 MiB response limit, preserving safe caching and representation
headers. Responses include `X-Palewire-Discovery-Proxy: cloudflare-worker-v1`.
Django's static build does not produce these routes. Cloudflare must keep the
Worker attached to all three routes for federation discovery to work.

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

#### Stage 1 incidents and safe retry

The first Stage 1 deploy on August 24, 2026 attached the routes before the
Worker was tested on Cloudflare. The Worker then returned `502` for every
matched route. The fixed Mastodon endpoints were healthy: WebFinger,
host-meta, and nodeinfo each returned `200` when contacted directly.

The Worker module exported the numeric `MAX_RESPONSE_BYTES` constant. Workerd
interprets module exports as Worker entries and only accepts functions or an
exported handler, so the module failed during startup before it made an
upstream request. At that time, deleting the Worker restored the Django
endpoints. This has been reproduced with Wrangler 4.125.0 and local Miniflare.
The regression test starts the bundled Worker in workerd, which catches invalid
module exports that direct TypeScript unit tests miss.

After the startup fix, the route-free workers.dev canary passed, but attaching
the Worker to the three `palewi.re` routes returned Worker-marked `502`
responses. `mastodon.palewi.re` is a proxied hostname in the same zone, so its
public fetch is a Worker-to-Worker subrequest. Cloudflare documents this as
[error 1042](https://developers.cloudflare.com/workers/observability/errors/)
and requires the
[`global_fetch_strictly_public`](https://developers.cloudflare.com/workers/configuration/compatibility-flags/#global-fetch-strictly-public)
compatibility flag. The flag is now declared in `wrangler.jsonc`.

The flag lets a public fetch enter the zone's routing. It must not allow the
upstream request to re-enter this Worker: Cloudflare's loop limit returns 1019
after 16 Worker invocations. The compiled production route plan is deliberately
limited to the exact `palewi.re` host, while the upstream is
`mastodon.palewi.re`; regression tests prove the three production patterns
cannot match that host. Do not add a `mastodon.palewi.re` route to this Worker.

The production Worker configuration intentionally has no production routes and
disables both workers.dev and preview URLs. The optional startup canary and the
same-zone canary use separate named environments and Worker names, with
workers.dev and preview URLs explicitly enabled for their route-free checks, so
neither can update a Worker serving production routes. The same-zone canary only accepts
`/.well-known/cloudflare-worker-canary` when its named environment provides the
`CANARY_PATH` binding. It fetches the same fixed upstream's NodeInfo endpoint.
The production Worker has no such binding and returns `404` for this path.

Miniflare starts the bundled Worker and catches module/runtime regressions, but
it cannot reproduce Cloudflare zone routing or error 1042. Passing the
same-zone canary below is therefore required before any production route is
attached.

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

# 2. Optional: deploy and verify a route-free workers.dev startup canary.
# The startup-canary environment explicitly re-enables public preview access.
# It confirms startup only; it cannot approve same-zone traffic.
CONFIRM_WORKER_CANARY_DEPLOY=1 make worker-canary-deploy
BASE_URL="https://the-url-printed-by-wrangler" make worker-verify-canary
CONFIRM_WORKER_DELETE_CANARY=1 make worker-delete-canary

# 3. Deploy a separate same-zone canary with no route, then attach only its
# non-production path.
CONFIRM_WORKER_SAME_ZONE_CANARY_DEPLOY=1 make worker-same-zone-canary-deploy
CONFIRM_WORKER_ATTACH_SAME_ZONE_CANARY=1 make worker-attach-same-zone-canary

# 4. Confirm the public same-zone fetch returns the Worker marker and NodeInfo.
BASE_URL="https://palewi.re" make worker-verify-same-zone-canary

# 5. Delete the same-zone canary, which also detaches its only route. Do not
# attach production routes unless this verification and cleanup both succeeded.
CONFIRM_WORKER_DELETE_SAME_ZONE_CANARY=1 make worker-delete-same-zone-canary

# 6. Attach and verify only the three production discovery routes.
CONFIRM_WORKER_ATTACH_ROUTES=1 make worker-attach-routes
make worker-verify-production
```

`worker-verify-canary` and `worker-verify-production` check valid requests for
all three discovery endpoints:

- WebFinger with `resource=acct:palewire@palewi.re` returns
  `application/jrd+json; charset=utf-8`.
- Host-meta returns `application/xrd+xml; charset=utf-8`.
- Nodeinfo returns `application/json; charset=utf-8`.

Each must return `200` and the exact
`X-Palewire-Discovery-Proxy: cloudflare-worker-v1` marker. The verifier is a
POSIX `/bin/sh` script and accepts `BASE_URL` for controlled local tests or a
canary. It uses bounded curl retries and, after route attachment, waits 15
seconds between up to four marker checks to allow Cloudflare propagation. It
fails immediately for a bad status or content type, and exits non-zero when the
marker never appears.

`worker-verify-same-zone-canary` is also a POSIX `/bin/sh` script. It checks
the canary's `200`, Worker marker, NodeInfo content type, and NodeInfo `links`
response. If a canary fails, do not attach the production routes. If production
verification fails with a bad status or content type, follow the emergency
recovery procedure below:

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

All deployment, attachment, and deletion commands are intentionally guarded.
They work with either `wrangler login` OAuth or `CLOUDFLARE_API_TOKEN`; no
token value appears in a command. Deleting either canary removes only that
separate Worker and its route. Deleting the production Worker removes its
attached routes. Django has no fallback for these routes.

### Legacy redirect Worker

`project/redirects.yaml` is the readable, validated source of truth for legacy
redirects. It currently has 22 exact paths and 8 dynamic patterns; this is the
full retired Django inventory (the issue's earlier 21/7 count was stale).
`project/redirect_manifest.py` is pure Python validation and route-plan tooling
used by the Worker tests, deployment commands, and production verifier.
`workers/legacy-redirects/` reads that same file as a bundled text module and
has no `fetch()` call. Its small explicit
`WorkerEnvironment` interface covers the only optional canary binding, avoiding
a second generated 15,000-line Workerd declaration while preserving strict
TypeScript and Wrangler dry-run validation. A matching request receives a
302, its manifest destination, and
`X-Palewire-Legacy-Redirect: cloudflare-worker-v1`. Queries are dropped.

The generated plan has 37 explicit `palewi.re` routes for the 30 manifest
entries. Every pattern has one terminal wildcard, which Cloudflare requires;
there are no infix wildcards and no `palewi.re/*` route. The root-level date
pattern uses ten digit-prefixed routes (`0*` through `9*`) because Cloudflare
cannot express four constrained path segments in one route. Those routes do
not match any current page, and the Worker returns 404 for a malformed suffix
instead of proxying to an origin. This Worker does not fetch a same-zone origin, so
`global_fetch_strictly_public` is neither needed nor enabled. Its tests assert
that redirect matches never create a subrequest.

The production smoke workflow runs the same verifier after deployment. It
checks every exact rule, two representative cases for
each dynamic rule, the exact `Location`, the Worker marker, and adjacent
non-legacy paths. It uses a 20-second curl timeout and waits 15 seconds between
up to four marker checks for route propagation.

Use a dedicated Cloudflare token for deployment, restricted to the owning
account and `palewi.re` zone. It needs only **Account > Workers Scripts >
Edit**, **Zone > Workers Routes > Edit**, and **Zone > Zone > Read**. The
read-only `make cloudflare-check` token remains limited to **User > User
Details > Read** and **User > Memberships > Read**. Store either token only as
`CLOUDFLARE_API_TOKEN`; keep the required account ID as
`CLOUDFLARE_ACCOUNT_ID`; never commit either value.

```bash
# Stage 1: local manifest, runtime, and configuration checks.
make legacy-worker-test
make legacy-worker-validate
make legacy-worker-route-plan

# Optional route-free startup canary. It cannot validate zone routing.
CONFIRM_LEGACY_WORKER_CANARY_DEPLOY=1 make legacy-worker-canary-deploy
# Verify the workers.dev URL printed by Wrangler with a representative redirect.
BASE_URL="https://the-url-printed-by-wrangler" scripts/verify-legacy-redirects.sh
CONFIRM_LEGACY_WORKER_DELETE_CANARY=1 make legacy-worker-delete-canary

# Required production-zone canary: deploy it without routes, then attach only
# /legacy-redirects-canary. It does not redirect and is disabled in production.
CONFIRM_LEGACY_WORKER_SAME_ZONE_CANARY_DEPLOY=1 make legacy-worker-same-zone-canary-deploy
CONFIRM_LEGACY_WORKER_ATTACH_SAME_ZONE_CANARY=1 make legacy-worker-attach-same-zone-canary
BASE_URL="https://palewi.re" make legacy-worker-verify-same-zone-canary
CONFIRM_LEGACY_WORKER_DELETE_SAME_ZONE_CANARY=1 make legacy-worker-delete-same-zone-canary

# Attach all generated production routes only after the canary is deleted.
CONFIRM_LEGACY_WORKER_ATTACH_ROUTES=1 make legacy-worker-attach-routes
# Bounded propagation-aware checks cover every exact path, two cases per
# dynamic pattern, Location, marker, and adjacent current paths.
WORKER_MARKER_ATTEMPTS=4 WORKER_MARKER_WAIT_SECONDS=15 make legacy-worker-verify-production
```

Every mutating command requires its named confirmation variable. The verifier
waits for the marker during route propagation but fails immediately on a bad
status or Location.

GitHub releases summarize meaningful batches of deployed changes. See
[RELEASING.md](RELEASING.md) for the changelog and release process.
