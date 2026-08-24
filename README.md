# palewi.re

Ben Welsh's personal site — a Django blog and portfolio at [palewi.re](https://palewi.re).

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/) for package management
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) for local setup and Heroku commands

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

`make bootstrap` checks both commands before it installs anything. For its
commands, it also adds common user installation paths including
`$HOME/.local/bin`, Heroku's user client directory, and a detected Homebrew
bin directory. It does not install either command or authenticate with Heroku.

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
system check, and the full pytest suite. CI uses the same Make targets.

To auto-format code:

```bash
make fmt
```

## Tests

```bash
make test
```

Tests and local serving do not require PostgreSQL or `DATABASE_URL`.

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

The Heroku CLI is available in Copilot cloud-agent sessions through the
official installer in `.github/workflows/copilot-setup-steps.yml`. Authentication
is not part of repository setup. For a cloud agent that must run authenticated
Heroku commands, add `HEROKU_API_KEY` as a GitHub Copilot Agents secret; never
store it in this repository.

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
