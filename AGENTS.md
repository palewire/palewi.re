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
  - `coltrane/content/`: YAML-backed bio-page content (awards, clips, docs, talks)
  - `coltrane/content_loaders.py`: validated loaders for all YAML content types
- `toolbox/`: shared utilities
- `project/`: Django settings and URL routing
- `tests/`: pytest suite

Use `uv` and `pyproject.toml` for Python dependencies, Ruff for formatting and
linting, and ty for static analysis.

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
```

Ordered by type, then alphabetically by title.

### bio_skills.yaml

Skills listed on `/who-is-ben-welsh/` under "Technical skills".

```yaml
skills:
  - "Skill description"
```

Order is preserved as written.
