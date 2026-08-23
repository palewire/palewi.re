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

# Install dependencies (creates .venv automatically)
make install

# Create local database
createdb palewire

# Apply migrations
make migrate

# Start server
make serve
```

Open <http://localhost:8000> in your browser.

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

This runs Ruff linting/formatting checks and the full pytest suite.

To auto-format code:

```bash
make fmt
```

## Tests

```bash
make test
```

Tests require a running PostgreSQL database. Set `DATABASE_URL` or rely on the default (`postgres://postgres@localhost/palewire`).

## Deployment

The app deploys to Heroku automatically when a pull request merges to `main` **after CI passes**.

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
