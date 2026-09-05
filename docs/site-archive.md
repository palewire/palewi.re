# Site archive

The site archive is a small, resumable inventory of public `palewi.re` HTML
pages and their Internet Archive availability. It is deliberately separate
from deployment and required CI. The durable source of truth is
`manifest.json` on the `site-archive-data` branch; the workflow also uploads
each run's manifest, state token, and report as a recovery artifact.

## Local commands

The default manifest is `.site-archive/manifest.json`. Build the site first
when using discovery (`make bake`).

```sh
uv run python -m scripts.site_archive discover \
  --manifest .site-archive/manifest.json --build-dir dist
uv run python -m scripts.site_archive verify \
  --manifest .site-archive/manifest.json --max-checks 100
uv run python -m scripts.site_archive capture \
  --manifest .site-archive/manifest.json --max-captures 10
uv run python -m scripts.site_archive report \
  --manifest .site-archive/manifest.json
uv run python -m scripts.site_archive sync \
  --manifest .site-archive/manifest.json --max-pages 100 \
  --max-checks 100 --max-captures 10 --max-seconds 900
```

The corresponding convenience targets are
`make site-archive-discover`, `make site-archive-verify`,
`make site-archive-capture`, `make site-archive-sync`, and
`make site-archive-report`. Add `--lookup-only` to `sync` when no capture
requests are allowed; lookup-only verification does not need Save Page Now
credentials.

Before submitting a capture, the tool checks that the page still serves public
HTML and checks Wayback again. It saves the pending request before contacting
the capture service, so an interrupted response does not lead to an immediate
duplicate submission. Availability lookups time out after 30 seconds; capture
requests have a separate 120-second timeout. Due pending captures are checked
before pages that have never been checked. A returned snapshot URL that differs
only by one trailing slash is accepted only after both live pages report the
requested canonical URL.

## Durable branch persistence

The branch commands use the authenticated `gh` CLI and never check out or
modify another worktree:

```sh
uv run python -m scripts.site_archive.branch fetch \
  --path .site-archive/manifest.json \
  --state-token .site-archive/state-token.json
uv run python -m scripts.site_archive.branch push \
  --path .site-archive/manifest.json \
  --state-token .site-archive/state-token.json
```

Only the `site-archive-data` branch is accepted; the repository defaults to
`palewire/palewi.re`. `fetch` records the exact commit head in the state token. A genuinely absent
branch produces an explicit missing token and a validated empty manifest.
Permission, authentication, malformed-response, and other API failures are not interpreted
as an absent branch.

`push` refuses a branch that changed after `fetch`. The first write creates an
orphan commit containing only `manifest.json`; later writes are non-forced
updates with the fetched commit as parent. The commit carries the required
Copilot App co-author trailer. Identical manifest bytes do not create an empty
commit. A failed write leaves the local manifest untouched. Never force-push,
delete, or manually edit the data branch. If a run has a stale token, fetch
again and reconcile the local work before retrying.

The workflow needs `contents: read` to fetch state and `contents: write` only
for the persistence job. Scheduled and manual runs are serialized so archive
writers cannot race each other. Configure
`SAVEPAGENOW_ACCESS_KEY` and `SAVEPAGENOW_SECRET_KEY` as repository or
environment secrets before enabling authenticated capture runs. They are
available only to the archive job and are never printed or written to state.

If the workflow fails after archive work, download its recovery artifact. Keep
the manifest and token together, inspect the report, and use a fresh `fetch`
before reconciling and pushing; do not force-push an artifact over a newer
branch head. Fetch into a fresh local directory so the recovery copy is not
overwritten. Reconcile its page records with the latest manifest, then push
using the newly fetched token.

After these code changes reach `main`, the weekly job runs on Mondays at
06:17 UTC. For the first run, use **Run workflow** with **lookup_only** enabled
to inspect the inventory without requesting captures. Then allow a small
authenticated run and inspect its pending confirmations before increasing
the capture limit. Local lookup-only commands work without credentials;
authenticated local commands require both Save Page Now variables in the
environment, or the worktree `.env` when using Make.

## Reading results and limitations

`unknown` means no archive lookup has completed, `missing` means a lookup
confirmed no snapshot, `pending` means a capture request awaits independent
confirmation, `archived` means a confirmed snapshot exists, and `blocked`
means capture is not currently possible. Service failures and malformed
responses are recorded as errors, not converted to `missing`; routine backlog
is different from an outage or configuration failure.

Discovery starts with the production build, the live sitemap, internal links,
and same-site documentation catalogs. Public documentation navigation is
followed when a sitemap is absent or unavailable. A docs sitemap returning
403, 404, or 410 is reported as an optional discovery gap so navigation can
continue; other discovery and service errors fail the run and remain visible
in the report. A docs site published by another repository may still have
unlinked pages that cannot be proven discoverable without that publisher's
complete inventory. Interrupted scans keep their queue and known URLs for a
later run.

A blocked page is not submitted again automatically. Resolve the stated
restriction first. To retry, fetch into a fresh directory, change that page's
`archive_status` to `unknown`, and clear `last_error` and `next_retry_at` in the
local manifest. Run verification before requesting another capture and push
the resulting state with its fetched token. Never mark a page archived without
confirmed snapshot evidence.

A confirmed HTML snapshot does **not** guarantee that JavaScript applications,
images, fonts, embedded video, downloadable PDFs, or other media will replay.
Use the separate media-preservation tooling for audio and video. This project
reuses any confirmed successful snapshot and does not refresh captures merely
because a newer one might exist.
