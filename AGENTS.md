# Agent guide

## Start here

Run `make bootstrap` once after creating a clone or worktree. It installs locked
dependencies and installs the pre-commit hooks. It first confirms that `uv`,
Node.js 24.22 or later in the Node 24 series, and npm are available. It
installs the locked Worker CLIs locally; it does not install a global CLI or
authenticate with Cloudflare.

Run the development server with `make serve`. It first builds the expanded
stylesheet and its source map. Linked worktrees automatically receive an
available local port.

When adding or changing a URL in `coltrane/content/clips.yaml`, load the
`archive-clips` skill and run `make archive-clips`. Every clip must retain the
resulting `archive_url` or a specific `archive_exemption`.

Run `make preservation-review` after adding or changing a clip, talk video, or
playable media in a post. It is offline and points to the exact source and
next preservation action. New private, DRM-protected, login-required, or
otherwise inaccessible media requires a specific recorded reason in
`preservation-review-baseline.json`; do not bypass access controls.

When running, auditing, or troubleshooting a local audio/video backup of the
media referenced by `coltrane/content/talks.yaml` or blog posts, load the
`archive-media` skill (`.github/skills/archive-media/SKILL.md`) first.

When creating browser-framed lead art for a post from a public URL, load the
`lead-art-screenshot` skill (`.github/skills/lead-art-screenshot/SKILL.md`).

## Before finishing

Run `make check`. This is the same set of lint, type, Django, and test checks
used by CI.

Before opening or merging a pull request, apply exactly one changelog category:
`feature`, `improvement`, `fix`, `maintenance`, or `skip-changelog`. The
required Lint check rejects pull requests without exactly one category.
`enhancement` counts as an improvement; Dependabot's `dependencies` and
`github_actions` labels count as maintenance. Read `RELEASING.md` before
creating a GitHub release. Releases use semantic versions, point to the
deployed `main` commit, and are published only after the production smoke test
passes.

All three Workers use project-local `cf` (pinned in each package.json) and
require Node.js 24.22 or later in the Node 24 series. Their settings and explicit
route attachment modes live in `cloudflare.config.ts`; production has no public
preview URLs, and only the named canary or static-site preview modes enable
them. Use their guarded Makefile targets for deploys and cleanup. `cf` needs its own OAuth login or
`CLOUDFLARE_API_TOKEN`. The Mastodon Worker uses Vite with pinned
`@cloudflare/vite-plugin` 2.0.0-beta.v.8 and Vite 8.3.5 for bundling and local
development. The legacy redirects Worker uses the same pinned Vite and
`@cloudflare/vite-plugin` versions with `cf dev` and `cf build`. Only the
static-site Worker still uses Wrangler as its bundler; Wrangler also supplies
the read-only identity check. Static asset build settings live in
`wrangler.config.ts`. The legacy production route mode calls the Python
redirect validator; keep that validator as the source of the deployed route
plan. Generated `.cloudflare/` build output and types must stay untracked.

Worker changes also require `make worker-test`, `make worker-validate`,
`make legacy-worker-test`, and `make legacy-worker-validate`. Production
configs keep workers.dev and preview URLs disabled; the named
`startup-canary` and `same-zone-canary` modes explicitly enable preview
URLs for guarded, route-free checks.

Keep changes focused. Add or update tests when behavior changes. Do not commit
secrets, generated files, or `.goals/` agent state.

## Project map

- `coltrane/`: publishing features and content
  - `coltrane/content/`: YAML-backed content (apps, awards, clips, code, docs, talks, slogans, bots)
  - `coltrane/content_loaders.py`: validated loaders for all YAML content types
- `toolbox/`: shared utilities
- `project/`: Django settings and URL routing
- `scripts/media_archive/`: preservation-only audio/video backup tooling (see below)
- `tests/`: pytest suite

Use `uv` and `pyproject.toml` for Python dependencies, plain CSS for styles,
Ruff for formatting and linting, and ty for static analysis.

Copilot cloud agents use the same locked Worker dependencies as local bootstrap.
For authenticated Cloudflare identity checks, add a least-privilege
`CLOUDFLARE_API_TOKEN` Copilot Agents secret with **User Details: Read** and
**Memberships: Read** permissions. Locally, run `npm exec -- wrangler login`
from `workers/static-site/` or set that environment variable, then use `make cloudflare-check`. This check uses
`wrangler whoami --json`; it does not need `CLOUDFLARE_ACCOUNT_ID` and must
not be expanded into a deployment command until a target is chosen.

The vendored Wrangler skill includes general installation advice. For this
repository, do not install global Wrangler or use `@latest`; run
`make bootstrap` for the locked Worker dependencies and `make check-wrangler`
to confirm the static-site package CLI. Worker commands use their own package
pins. Relative `UV_ENV_FILE` paths resolve from the repository root, including
commands that change into Worker directories.

## YAML content types

Bio-page content lives in `coltrane/content/` as YAML files. Each file is
validated on load; a bad record raises `ContentError` with a clear message.

### awards.yaml

Honors listed on `/who-is-ben-welsh/` under "Honors".

```yaml
awards:
  - title: "Award name"
    url: "https://..."       # optional
    year: 2024               # optional integer
```

Ordered by descending year, then alphabetically by title.

### clips.yaml

Published work records are routed by type: `story` and newsroom `app` records
appear on `/clips/`, standalone `service` records on `/apps/`, `software`
records on `/code/`, and `lesson-plan` records on `/guides/`.

```yaml
clips:
  - title: "Story title"
    type: story              # app | lesson-plan | story | software
    date: "2024-06-15"       # YYYY-MM-DD
    url: "https://..."       # must be unique across all clips
    archive_url: "https://web.archive.org/web/..." # Wayback snapshot
```

Ordered by descending date.

Run `make archive-clips` after adding or changing a URL. The command reuses an
existing snapshot when possible and otherwise uses `SAVEPAGENOW_ACCESS_KEY`
and `SAVEPAGENOW_SECRET_KEY` to create one. Use `archive_exemption` instead of
`archive_url` only when Wayback cannot capture the page.

### talks.yaml

Talks listed on `/talks/`.

```yaml
talks:
  - title: "Talk title"
    venue: "Conference name"
    location: "City, State"
    date: "2024-06-15"       # YYYY-MM-DD
    video_url: "https://..." # optional
    slides_url: "https://..." # optional
    guide_url: "https://..." # optional related guide
    deck_aspect_ratio: 16 / 9 # optional embedded desktop ratio
    deck_mobile_aspect_ratio: 9 / 16 # optional mobile ratio
    archive_url: "https://web.archive.org/web/..." # optional Wayback snapshot
```

Ordered by descending date.

### docs.yaml

Documentation listed in two catalogs: software on `/code/` and lesson plans on
`/guides/`.

```yaml
docs:
  - title: "Package name"
    type: software           # lesson-plan | software
    url: "https://..."       # must be unique across all docs
    description: "..."       # optional
    repository_url: "https://..." # optional canonical source repository; unique if set
```

`repository_url` must be an HTTP(S) URL. Omit it or use an empty value when a
canonical repository cannot be verified. It is catalog metadata and is not
rendered on the list pages. Docs are ordered by type, then alphabetically by
title.

### bio_skills.yaml

Skills listed on `/who-is-ben-welsh/` under "Technical skills".

```yaml
skills:
  - "Skill description"
```

Order is preserved as written.

### slogans.yaml

Short phrases that appear in the site header. Each entry has one required field.

```yaml
slogans:
  - title: "phrase here"
```

Ordered alphabetically by title. Titles must be non-empty strings. An empty
list is valid.  Use `random_slogan()` from `coltrane.content_loaders` to pick
one at random for display.

### bots.yaml

Automated accounts listed on `/bots/`. Each entry requires `title` and
`mastodon_url`; `twitter_url` is optional and defaults to an empty string.

```yaml
bots:
  - title: "@BotName"
    mastodon_url: "https://mastodon.example.com/@botname"  # required, unique
    twitter_url: "https://twitter.com/botname"             # optional, unique if set
```

Order is preserved as written (no automatic sorting). Both `mastodon_url` and
non-empty `twitter_url` values must be unique across the list. URLs must start
with `http`.

## Media archive (audio/video backup)

`scripts/media_archive/` is a preservation-only backup tool for the
audio/video referenced by `coltrane/content/talks.yaml` and blog posts under
`coltrane/content/posts/`, tracked in issue #176 ("Back up video embeds
locally"). Load `.github/skills/archive-media/SKILL.md` before running it.

Key rules for agents:

- Binaries and the manifest live **only** under a user-chosen
  `--archive-root` / `MEDIA_ARCHIVE_PATH` directory **outside** this
  repository. The CLI refuses any path inside the repo. Never write media
  under a repo static path, and never commit media or a manifest.
- It uses `yt-dlp` (a `dev` dependency group package) as the extractor and
  downloader, plus `ffmpeg` only when a source needs stream muxing (YouTube,
  Vimeo, unrecognized hosts). `ffmpeg` is intentionally excluded from
  `make bootstrap`; install it only when actually backing up those kinds.
- It never bypasses DRM, private access, login requirements, or other
  controls — a source that requires that is expected to fail, and the
  failure is recorded, not retried automatically forever.
- `make media-archive-inventory` is network-free and safe to run any time.
  `make media-archive-backup` (with `ARCHIVE_ROOT=...` or `MEDIA_ARCHIVE_PATH`
  set) downloads pending/failed candidates and is idempotent/resumable.
  `uv run python -m scripts.media_archive verify --archive-root ...` is an
  offline checksum audit.
- Do not add GitHub Actions schedules, R2/S3 configuration, or Django
  static-file storage for this tool — it is a manual/local maintenance
  script by design.
- Do not close issue #176 just because this tooling exists; close it only
  after a real, durable backup run has actually completed.
