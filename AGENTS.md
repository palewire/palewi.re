# Agent guide

## Start here

Run `make bootstrap` once after creating a clone or worktree. It installs locked
dependencies and installs the pre-commit hooks. It first confirms that `uv`,
the Heroku CLI, and Wrangler are available; it does not install or authenticate
any tool.

Run the development server with `make serve`. Linked worktrees automatically
receive an available local port.

## Before finishing

Run `make check`. This is the same set of lint, type, Django, and test checks
used by CI.

Keep changes focused. Add or update tests when behavior changes. Do not commit
secrets, generated files, or `.goals/` agent state.

## Project map

- `coltrane/`: publishing features and content
  - `coltrane/content/`: YAML-backed content (awards, clips, docs, talks, slogans, bots)
  - `coltrane/content_loaders.py`: validated loaders for all YAML content types
- `toolbox/`: shared utilities
- `project/`: Django settings and URL routing
- `tests/`: pytest suite

Use `uv` and `pyproject.toml` for Python dependencies, Ruff for formatting and
linting, and ty for static analysis.

Copilot cloud agents receive `uv` and the Heroku CLI from
`.github/workflows/copilot-setup-steps.yml`. Authentication remains
user-provided. If a cloud agent needs authenticated Heroku access, use a
`HEROKU_API_KEY` GitHub Copilot Agents secret, never repository data.

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
```

Ordered by descending date.

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
