# palewi.re

Ben Welsh's personal site — a Django blog and portfolio at [palewi.re](https://palewi.re).

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/) for package management
- PostgreSQL 14+

## Setup

```bash
# Clone
git clone https://github.com/palewire/palewi.re.git
cd palewi.re

# Install dependencies, create the database, and apply migrations
make bootstrap

# Start server
make serve
```

Open the URL printed by the server. Linked Git worktrees automatically use
separate PostgreSQL databases and available local ports, so multiple agents can
run the site at the same time.

## Environment variables

| Variable | Required in prod | Description |
|----------|-----------------|-------------|
| `SECRET_KEY` | Yes | Django secret key |
| `DATABASE_URL` | No (defaults to local) | PostgreSQL connection string |
| `PRODUCTION` | No | Set `true` to enable production security |
| `DEBUG` | No | Set `false` to disable debug output |

## Quality gate

Run the complete quality gate before opening a pull request:

```bash
make check
```

This runs Ruff linting and formatting checks, ty static analysis, Django's
system and migration checks, and the full pytest suite. CI uses the same Make
targets.

To auto-format code:

```bash
make fmt
```

## Tests

```bash
make test
```

Tests require a running PostgreSQL database. Set `DATABASE_URL` or rely on the
default: `postgres://postgres@localhost/palewire` in a normal clone, or an
automatically named isolated database in a linked worktree.

## Blog post Markdown

Public posts in `coltrane/content/posts/` are one `.md` file each. Their YAML
front matter requires `title`, `slug`, and `published_at`; the datetime must
use the Los Angeles offset. `repr_image` and `wordpress_id` are optional.
Keep the body as raw HTML, including any `<pre lang="...">` code blocks. Do
not add drafts or a status field. The filename format is
`YYYY-MM-DD--slug.md`, and `posts-manifest.json` is the checked-in public
fingerprint generated during the production export.

## Deployment

The app deploys to Heroku automatically when a pull request merges to `main` **after CI passes**.

GitHub releases summarize meaningful batches of deployed changes. See
[RELEASING.md](RELEASING.md) for the changelog and release process.

**Rollback** a bad deploy:

```bash
heroku releases
heroku rollback vN   # where N is the last good release number
```

**Manual migration** (if needed):

```bash
heroku run python manage.py migrate
```

## Health check

A lightweight health endpoint is available at `/health/`. It returns HTTP 200 and `{"status": "ok", "db": true}` when the database is reachable.
