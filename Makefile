# palewi.re Makefile

export UV_NO_ENV_FILE = 1

HOMEBREW_BIN := $(shell for path in /opt/homebrew/bin /usr/local/bin; do test -x "$$path/brew" && { printf '%s' "$$path"; break; }; done)
WRANGLER_VERSION := 4.125.0
export PATH := $(HOME)/.local/bin:$(HOME)/.local/share/heroku/client/bin:$(HOME)/.npm-global/bin:$(HOME)/.volta/bin:$(HOME)/.asdf/shims:$(HOME)/.fnm/current/bin:$(HOMEBREW_BIN):$(PATH)

.PHONY: help bootstrap ci-bootstrap check-tools check-wrangler cloudflare-check install hooks serve check test lint typecheck django-check fmt

help:
	@echo "Available targets:"
	@echo "  bootstrap  Check developer tools, then prepare dependencies and hooks"
	@echo "  ci-bootstrap  Prepare dependencies for CI"
	@echo "  check-tools  Confirm uv, the Heroku CLI, and Wrangler are available"
	@echo "  check-wrangler  Confirm Wrangler is available"
	@echo "  cloudflare-check  Show the authenticated Cloudflare account"
	@echo "  install    Install all dependencies without changing Git hooks"
	@echo "  hooks      Install pre-commit hooks"
	@echo "  serve      Start the development server"
	@echo "  check      Run the same lint, type, Django, and test checks as CI"
	@echo "  test       Run tests only"
	@echo "  lint       Run Ruff linter and format check"
	@echo "  typecheck  Run ty static type analysis"
	@echo "  fmt        Auto-format with Ruff"

install:
	@"$$(command -v uv)" sync --locked --group dev

hooks:
	@"$$(command -v uv)" run pre-commit install

check-tools:
	@command -v uv > /dev/null || { echo "uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/" >&2; exit 1; }
	@command -v heroku > /dev/null || { echo "The Heroku CLI is required. Install it from https://devcenter.heroku.com/articles/heroku-cli#install-the-heroku-cli" >&2; exit 1; }
	@$(MAKE) --no-print-directory check-wrangler

check-wrangler:
	@command -v wrangler > /dev/null || { echo "Wrangler is required. Install version $(WRANGLER_VERSION) with: npm install --global wrangler@$(WRANGLER_VERSION)" >&2; exit 1; }
	@"$$(command -v wrangler)" --version
	@version="$$("$$(command -v wrangler)" --version | awk 'match($$0, /[0-9]+\.[0-9]+\.[0-9]+/) { print substr($$0, RSTART, RLENGTH); exit }')"; \
	test "$$version" = "$(WRANGLER_VERSION)" || { echo "Wrangler $(WRANGLER_VERSION) is required. Found $${version:-an unrecognized version}. Install it with: npm install --global wrangler@$(WRANGLER_VERSION)" >&2; exit 1; }

cloudflare-check: check-wrangler
	@"$$(command -v wrangler)" whoami --json || { echo "Cloudflare authentication failed. Run 'wrangler login' locally or set CLOUDFLARE_API_TOKEN." >&2; exit 1; }

bootstrap: check-tools install hooks

ci-bootstrap: install

serve:
	@"$$(command -v uv)" run python -m scripts.worktree serve

check: lint typecheck django-check test

test:
	@"$$(command -v uv)" run pytest tests/

lint:
	@"$$(command -v uv)" run ruff check .
	@"$$(command -v uv)" run ruff format --check .

typecheck:
	@"$$(command -v uv)" run ty check .

django-check:
	@"$$(command -v uv)" run python manage.py check

fmt:
	@"$$(command -v uv)" run ruff check --fix .
	@"$$(command -v uv)" run ruff format .
