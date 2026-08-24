# palewi.re Makefile

export UV_NO_ENV_FILE = 1

HOMEBREW_BIN := $(shell for path in /opt/homebrew/bin /usr/local/bin; do test -x "$$path/brew" && { printf '%s' "$$path"; break; }; done)
WRANGLER_VERSION := 4.125.0
export PATH := $(HOME)/.local/bin:$(HOME)/.local/share/heroku/client/bin:$(HOME)/.npm-global/bin:$(HOME)/.volta/bin:$(HOME)/.asdf/shims:$(HOME)/.fnm/current/bin:$(HOMEBREW_BIN):$(PATH)

WORKER_DIR := workers/mastodon-well-known-proxy
WORKER_CANARY_NAME := palewire-mastodon-well-known-proxy-canary
WORKER_ROUTES := --route palewi.re/.well-known/webfinger* --route palewi.re/.well-known/host-meta* --route palewi.re/.well-known/nodeinfo*
WORKER_SAME_ZONE_CANARY_ROUTE := palewi.re/.well-known/cloudflare-worker-canary
LEGACY_WORKER_DIR := workers/legacy-redirects
LEGACY_WORKER_CANARY_NAME := palewire-legacy-redirects-canary
LEGACY_WORKER_SAME_ZONE_CANARY_ROUTE := palewi.re/legacy-redirects-canary*

.PHONY: help bootstrap ci-bootstrap check-tools check-wrangler cloudflare-check install hooks css css-dev serve check test lint typecheck django-check fmt archive-clips check-clip-archives media-archive-inventory media-archive-backup media-archive-verify worker-test worker-validate worker-canary-deploy worker-verify-canary worker-delete-canary worker-same-zone-canary-deploy worker-attach-same-zone-canary worker-verify-same-zone-canary worker-delete-same-zone-canary worker-route-plan worker-attach-routes worker-verify-production worker-detach-routes worker-delete legacy-worker-test legacy-worker-validate legacy-worker-canary-deploy legacy-worker-delete-canary legacy-worker-same-zone-canary-deploy legacy-worker-attach-same-zone-canary legacy-worker-verify-same-zone-canary legacy-worker-delete-same-zone-canary legacy-worker-route-plan legacy-worker-attach-routes legacy-worker-verify-production legacy-worker-detach-routes legacy-worker-delete

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
	@echo "  archive-clips  Archive clip URLs missing Wayback metadata"
	@echo "  check-clip-archives  Confirm every clip has Wayback metadata"
	@echo "  media-archive-inventory  List discovered talk/post media without downloading anything"
	@echo "  media-archive-backup  Back up pending media to ARCHIVE_ROOT (or MEDIA_ARCHIVE_PATH)"
	@echo "  media-archive-verify  Recompute checksums of already-archived media, offline"
	@echo "  worker-test  Install locked Worker dependencies and run Worker tests"
	@echo "  worker-validate  Type-check and dry-run the Worker without deploying"
	@echo "  worker-canary-deploy  Deploy a route-free Worker canary after explicit confirmation"
	@echo "  worker-verify-canary  Confirm a canary URL served all Worker endpoints"
	@echo "  worker-delete-canary  Delete the canary Worker after explicit confirmation"
	@echo "  worker-same-zone-canary-deploy  Deploy a route-free, same-zone canary Worker"
	@echo "  worker-attach-same-zone-canary  Attach the guarded same-zone canary route"
	@echo "  worker-verify-same-zone-canary  Confirm the same-zone canary marker and NodeInfo"
	@echo "  worker-delete-same-zone-canary  Delete the same-zone canary and its route"
	@echo "  worker-attach-routes  Attach production routes after explicit confirmation"
	@echo "  worker-verify-production  Confirm production served all Worker endpoints"
	@echo "  worker-detach-routes  Delete the Worker to detach its routes after explicit confirmation"
	@echo "  worker-delete  Delete the Worker and any attached routes after explicit confirmation"
	@echo "  legacy-worker-test  Install locked redirect Worker dependencies and run Worker tests"
	@echo "  legacy-worker-validate  Type-check, startup-check, and dry-run the redirect Worker"
	@echo "  legacy-worker-canary-deploy  Deploy a route-free redirect Worker canary after confirmation"
	@echo "  legacy-worker-same-zone-canary-deploy  Deploy a harmless same-zone redirect Worker canary"
	@echo "  legacy-worker-attach-same-zone-canary  Attach the harmless canary path after confirmation"
	@echo "  legacy-worker-verify-same-zone-canary  Confirm the same-zone canary marker"
	@echo "  legacy-worker-route-plan  Print the narrow production redirect route plan"
	@echo "  legacy-worker-attach-routes  Attach production redirect routes after confirmation"
	@echo "  legacy-worker-verify-production  Verify all redirects and adjacent untouched paths"
	@echo "  legacy-worker-detach-routes  Delete the redirect Worker and detach routes after confirmation"

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

check: lint typecheck django-check check-clip-archives test

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

archive-clips:
	@"$$(command -v uv)" run python -m scripts.archive_clips archive

check-clip-archives:
	@"$$(command -v uv)" run python -m scripts.archive_clips check

media-archive-inventory:
	@"$$(command -v uv)" run python -m scripts.media_archive inventory

media-archive-backup:
	@test -n "$$ARCHIVE_ROOT$$MEDIA_ARCHIVE_PATH" || { echo "Set ARCHIVE_ROOT=/path/outside/repo (or export MEDIA_ARCHIVE_PATH) to a directory outside this repository." >&2; exit 1; }
	@"$$(command -v uv)" run python -m scripts.media_archive backup $(if $(ARCHIVE_ROOT),--archive-root "$(ARCHIVE_ROOT)",)

media-archive-verify:
	@test -n "$$ARCHIVE_ROOT$$MEDIA_ARCHIVE_PATH" || { echo "Set ARCHIVE_ROOT=/path/outside/repo (or export MEDIA_ARCHIVE_PATH) to a directory outside this repository." >&2; exit 1; }
	@"$$(command -v uv)" run python -m scripts.media_archive verify $(if $(ARCHIVE_ROOT),--archive-root "$(ARCHIVE_ROOT)",)

worker-test:
	npm --prefix "$(WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	npm --prefix "$(WORKER_DIR)" run test

worker-validate:
	npm --prefix "$(WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	npm --prefix "$(WORKER_DIR)" run validate

worker-canary-deploy:
	@test "$$CONFIRM_WORKER_CANARY_DEPLOY" = "1" || { echo "Set CONFIRM_WORKER_CANARY_DEPLOY=1 after running make worker-validate." >&2; exit 1; }
	npm --prefix "$(WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	cd "$(WORKER_DIR)" && npm exec -- wrangler deploy --env startup-canary --strict --name "$(WORKER_CANARY_NAME)"

worker-verify-canary:
	@BASE_URL="$${BASE_URL:?Set BASE_URL to the workers.dev or preview URL printed by worker-canary-deploy.}" scripts/verify-worker-endpoints.sh

worker-delete-canary:
	@test "$$CONFIRM_WORKER_DELETE_CANARY" = "1" || { echo "Set CONFIRM_WORKER_DELETE_CANARY=1 to delete the route-free canary Worker." >&2; exit 1; }
	npm --prefix "$(WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	cd "$(WORKER_DIR)" && npm exec -- wrangler delete "$(WORKER_CANARY_NAME)" --force

worker-same-zone-canary-deploy:
	@test "$$CONFIRM_WORKER_SAME_ZONE_CANARY_DEPLOY" = "1" || { echo "Set CONFIRM_WORKER_SAME_ZONE_CANARY_DEPLOY=1 after make worker-validate passes." >&2; exit 1; }
	npm --prefix "$(WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	cd "$(WORKER_DIR)" && npm exec -- wrangler deploy --env same-zone-canary --strict

worker-attach-same-zone-canary:
	@test "$$CONFIRM_WORKER_ATTACH_SAME_ZONE_CANARY" = "1" || { echo "Set CONFIRM_WORKER_ATTACH_SAME_ZONE_CANARY=1 after the route-free same-zone canary deploy passes." >&2; exit 1; }
	npm --prefix "$(WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	cd "$(WORKER_DIR)" && npm exec -- wrangler deploy --env same-zone-canary --strict --route "$(WORKER_SAME_ZONE_CANARY_ROUTE)"

worker-verify-same-zone-canary:
	@BASE_URL="$${BASE_URL:-https://palewi.re}" scripts/verify-worker-same-zone-canary.sh

worker-delete-same-zone-canary:
	@test "$$CONFIRM_WORKER_DELETE_SAME_ZONE_CANARY" = "1" || { echo "Set CONFIRM_WORKER_DELETE_SAME_ZONE_CANARY=1 to delete the same-zone canary and detach its route." >&2; exit 1; }
	npm --prefix "$(WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	cd "$(WORKER_DIR)" && npm exec -- wrangler delete --env same-zone-canary --force

worker-route-plan:
	@printf '%s\n' "$(WORKER_ROUTES)"

worker-attach-routes:
	@test "$$CONFIRM_WORKER_ATTACH_ROUTES" = "1" || { echo "Set CONFIRM_WORKER_ATTACH_ROUTES=1 only after same-zone canary verification and cleanup pass." >&2; exit 1; }
	npm --prefix "$(WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	cd "$(WORKER_DIR)" && npm exec -- wrangler deploy --env="" --strict $(WORKER_ROUTES)

worker-verify-production:
	@scripts/verify-worker-endpoints.sh

worker-detach-routes:
	@test "$$CONFIRM_WORKER_DETACH_ROUTES" = "1" || { echo "Set CONFIRM_WORKER_DETACH_ROUTES=1 to delete the Worker and detach its routes." >&2; exit 1; }
	npm --prefix "$(WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	cd "$(WORKER_DIR)" && npm exec -- wrangler delete --env="" --force

worker-delete:
	@test "$$CONFIRM_WORKER_DELETE" = "1" || { echo "Set CONFIRM_WORKER_DELETE=1 to delete the Worker and any attached routes." >&2; exit 1; }
	npm --prefix "$(WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	cd "$(WORKER_DIR)" && npm exec -- wrangler delete --env="" --force

legacy-worker-test:
	npm --prefix "$(LEGACY_WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	npm --prefix "$(LEGACY_WORKER_DIR)" run test

legacy-worker-validate:
	npm --prefix "$(LEGACY_WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	npm --prefix "$(LEGACY_WORKER_DIR)" run validate

legacy-worker-canary-deploy:
	@test "$$CONFIRM_LEGACY_WORKER_CANARY_DEPLOY" = "1" || { echo "Set CONFIRM_LEGACY_WORKER_CANARY_DEPLOY=1 after make legacy-worker-validate." >&2; exit 1; }
	npm --prefix "$(LEGACY_WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	cd "$(LEGACY_WORKER_DIR)" && npm exec -- wrangler deploy --env startup-canary --strict --name "$(LEGACY_WORKER_CANARY_NAME)"

legacy-worker-delete-canary:
	@test "$$CONFIRM_LEGACY_WORKER_DELETE_CANARY" = "1" || { echo "Set CONFIRM_LEGACY_WORKER_DELETE_CANARY=1 to delete the route-free canary Worker." >&2; exit 1; }
	npm --prefix "$(LEGACY_WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	cd "$(LEGACY_WORKER_DIR)" && npm exec -- wrangler delete "$(LEGACY_WORKER_CANARY_NAME)" --force

legacy-worker-same-zone-canary-deploy:
	@test "$$CONFIRM_LEGACY_WORKER_SAME_ZONE_CANARY_DEPLOY" = "1" || { echo "Set CONFIRM_LEGACY_WORKER_SAME_ZONE_CANARY_DEPLOY=1 after make legacy-worker-validate passes." >&2; exit 1; }
	npm --prefix "$(LEGACY_WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	cd "$(LEGACY_WORKER_DIR)" && npm exec -- wrangler deploy --env same-zone-canary --strict

legacy-worker-attach-same-zone-canary:
	@test "$$CONFIRM_LEGACY_WORKER_ATTACH_SAME_ZONE_CANARY" = "1" || { echo "Set CONFIRM_LEGACY_WORKER_ATTACH_SAME_ZONE_CANARY=1 after the route-free same-zone canary deploy passes." >&2; exit 1; }
	npm --prefix "$(LEGACY_WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	cd "$(LEGACY_WORKER_DIR)" && npm exec -- wrangler deploy --env same-zone-canary --strict --route "$(LEGACY_WORKER_SAME_ZONE_CANARY_ROUTE)"

legacy-worker-verify-same-zone-canary:
	@BASE_URL="$${BASE_URL:-https://palewi.re}" scripts/verify-legacy-redirect-canary.sh

legacy-worker-delete-same-zone-canary:
	@test "$$CONFIRM_LEGACY_WORKER_DELETE_SAME_ZONE_CANARY" = "1" || { echo "Set CONFIRM_LEGACY_WORKER_DELETE_SAME_ZONE_CANARY=1 to delete the same-zone canary and detach its route." >&2; exit 1; }
	npm --prefix "$(LEGACY_WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	cd "$(LEGACY_WORKER_DIR)" && npm exec -- wrangler delete --env same-zone-canary --force

legacy-worker-route-plan:
	@uv run python -c 'from project.redirect_manifest import RULES, cloudflare_route_plan; print(" ".join(f"--route {route}" for route in cloudflare_route_plan(RULES)))'

legacy-worker-attach-routes:
	@test "$$CONFIRM_LEGACY_WORKER_ATTACH_ROUTES" = "1" || { echo "Set CONFIRM_LEGACY_WORKER_ATTACH_ROUTES=1 only after same-zone canary verification and cleanup pass." >&2; exit 1; }
	npm --prefix "$(LEGACY_WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	@routes="$$(uv run python -c 'from project.redirect_manifest import RULES, cloudflare_route_plan; print(" ".join(f"--route {route}" for route in cloudflare_route_plan(RULES)))')"; cd "$(LEGACY_WORKER_DIR)" && npm exec -- wrangler deploy --env="" --strict $$routes

legacy-worker-verify-production:
	@scripts/verify-legacy-redirects.sh

legacy-worker-detach-routes:
	@test "$$CONFIRM_LEGACY_WORKER_DETACH_ROUTES" = "1" || { echo "Set CONFIRM_LEGACY_WORKER_DETACH_ROUTES=1 to delete the Worker and detach its routes." >&2; exit 1; }
	npm --prefix "$(LEGACY_WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	cd "$(LEGACY_WORKER_DIR)" && npm exec -- wrangler delete --env="" --force

legacy-worker-delete:
	@test "$$CONFIRM_LEGACY_WORKER_DELETE" = "1" || { echo "Set CONFIRM_LEGACY_WORKER_DELETE=1 to delete the Worker and any attached routes." >&2; exit 1; }
	npm --prefix "$(LEGACY_WORKER_DIR)" ci --ignore-scripts --no-audit --no-fund
	cd "$(LEGACY_WORKER_DIR)" && npm exec -- wrangler delete --env="" --force
