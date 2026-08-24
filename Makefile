# palewi.re Makefile

export UV_NO_ENV_FILE = 1

HOMEBREW_BIN := $(shell for path in /opt/homebrew/bin /usr/local/bin; do test -x "$$path/brew" && { printf '%s' "$$path"; break; }; done)
WRANGLER_VERSION := 4.125.0
export PATH := $(HOME)/.local/bin:$(HOME)/.local/share/heroku/client/bin:$(HOME)/.npm-global/bin:$(HOME)/.volta/bin:$(HOME)/.asdf/shims:$(HOME)/.fnm/current/bin:$(HOMEBREW_BIN):$(PATH)

WORKER_DIR := workers/mastodon-well-known-proxy

.PHONY: help bootstrap ci-bootstrap check-tools check-wrangler cloudflare-check install hooks css css-dev serve check test lint typecheck django-check fmt worker-test worker-validate worker-deploy worker-verify-production worker-rollback

help:
	@echo "Available targets:"
	@echo "  bootstrap  Check developer tools, then prepare dependencies and hooks"
	@echo "  ci-bootstrap  Prepare dependencies for CI"
	@echo "  check-tools  Confirm uv, the Heroku CLI, and Wrangler are available"
	@echo "  check-wrangler  Confirm Wrangler is available"
	@echo "  cloudflare-check  Show the authenticated Cloudflare account"
	@echo "  install    Install all dependencies without changing Git hooks"
	@echo "  hooks      Install pre-commit hooks"
	@echo "  css        Build compressed production CSS"
	@echo "  css-dev    Build expanded CSS with a source map"
	@echo "  serve      Start the development server"
	@echo "  check      Run the same lint, type, Django, and test checks as CI"
	@echo "  test       Run tests only"
	@echo "  lint       Run Ruff linter and format check"
	@echo "  typecheck  Run ty static type analysis"
	@echo "  fmt        Auto-format with Ruff"
	@echo "  worker-test  Install locked Worker dependencies and run Worker tests"
	@echo "  worker-validate  Type-check and dry-run the Worker without deploying"
	@echo "  worker-deploy  Deploy the Worker after explicit confirmation"
	@echo "  worker-verify-production  Confirm production served the Worker marker"
	@echo "  worker-rollback  Roll back the Worker after explicit confirmation"

install:
	@"$$(command -v uv)" sync --locked --group dev
	@"$$(command -v npm)" ci

hooks:
	@"$$(command -v uv)" run pre-commit install

check-tools:
	@command -v uv > /dev/null || { echo "uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/" >&2; exit 1; }
	@command -v node > /dev/null || { echo "Node.js 24 is required. Install it from https://nodejs.org/" >&2; exit 1; }
	@command -v npm > /dev/null || { echo "npm is required. Install Node.js 24 from https://nodejs.org/" >&2; exit 1; }
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

css:
	@"$$(command -v npm)" run build:css

css-dev:
	@"$$(command -v npm)" run build:css:dev

serve: css-dev
	@"$$(command -v uv)" run python -m scripts.worktree serve

check: lint typecheck django-check test

test: css
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

worker-test:
	npm --prefix "$(WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	npm --prefix "$(WORKER_DIR)" run test

worker-validate:
	npm --prefix "$(WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	npm --prefix "$(WORKER_DIR)" run validate

worker-deploy:
	@test "$$CONFIRM_WORKER_DEPLOY" = "1" || { echo "Set CONFIRM_WORKER_DEPLOY=1 after running make worker-validate." >&2; exit 1; }
	npm --prefix "$(WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	npm --prefix "$(WORKER_DIR)" run deploy

worker-verify-production:
	@url="$${BASE_URL:-https://palewi.re}/.well-known/webfinger?resource=acct%3Apalewire%40palewi.re"; \
	response="$$(curl --silent --show-error --max-time 20 --dump-header - --output /dev/null --write-out '\n%{http_code}' "$$url)" || { echo "Production verification request failed." >&2; exit 1; }; \
	status="$$(printf '%s\n' "$$response" | tail -1)"; \
	headers="$$(printf '%s\n' "$$response" | sed '$$d')"; \
	test "$$status" = "200" || { printf '%s\n' "$$headers"; echo "Expected HTTP 200, received $$status." >&2; exit 1; }; \
	printf '%s\n' "$$headers"; \
	printf '%s\n' "$$headers" | tr -d '\r' | grep -qi '^x-palewire-discovery-proxy: cloudflare-worker-v1$$' || { echo "Worker response marker was not found." >&2; exit 1; }

worker-rollback:
	@test "$$CONFIRM_WORKER_ROLLBACK" = "1" || { echo "Set CONFIRM_WORKER_ROLLBACK=1 to remove the three Worker routes." >&2; exit 1; }
	npm --prefix "$(WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	CONFIRM_WORKER_ROLLBACK="$$CONFIRM_WORKER_ROLLBACK" npm --prefix "$(WORKER_DIR)" run disable-routes
