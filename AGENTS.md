# Agent guide

## Start here

Run `make bootstrap` once after creating a clone or worktree. It installs locked
dependencies and installs the pre-commit hooks. It first confirms that `uv`,
Node.js, npm, and Wrangler are available; it does not install or authenticate
any tool.

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

## Before finishing

Run `make check`. This is the same set of lint, type, Django, and test checks
used by CI.

Worker changes also require `make worker-test`, `make worker-validate`,
`make legacy-worker-test`, and `make legacy-worker-validate`. Production
Wrangler configs keep `workers_dev` and `preview_urls` disabled; the named
`startup-canary` and `same-zone-canary` environments explicitly enable preview
URLs for guarded, route-free checks.

Keep changes focused. Add or update tests when behavior changes. Do not commit
secrets, generated files, or `.goals/` agent state.

## Project map

- `coltrane/`: publishing features and content
  - `coltrane/content/`: YAML-backed content (awards, clips, docs, talks, slogans, bots)
  - `coltrane/content_loaders.py`: validated loaders for all YAML content types
- `toolbox/`: shared utilities
- `project/`: Django settings and URL routing
- `scripts/media_archive/`: preservation-only audio/video backup tooling (see below)
- `tests/`: pytest suite

Use `uv` and `pyproject.toml` for Python dependencies, the locked Dart Sass npm
dependency for CSS, Ruff for formatting and linting, and ty for static analysis.

Copilot cloud agents also receive Wrangler 4.125.0 from that setup workflow.
For authenticated Cloudflare identity checks, add a least-privilege
`CLOUDFLARE_API_TOKEN` Copilot Agents secret with **User Details: Read** and
**Memberships: Read** permissions. Locally, run `wrangler login` or set that
environment variable, then use `make cloudflare-check`. This check uses
`wrangler whoami --json`; it does not need `CLOUDFLARE_ACCOUNT_ID` and must
not be expanded into a deployment command until a target is chosen.

The vendored Wrangler skill includes general installation advice. For this
repository, do not install Wrangler from an agent or use `@latest`; run
`make check-wrangler` and use the existing pinned 4.125.0 CLI instead. Local
developers install it once outside the repository as documented in `README.md`.

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

Work items listed on `/work/`.

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
```

Ordered by descending date.

### docs.yaml

Documentation listed on `/docs/` in two groups.

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
rendered on `/docs/`. Docs are ordered by type, then alphabetically by title.

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
