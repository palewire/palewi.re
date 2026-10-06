# Preservation policy and runbook

## Purpose and boundaries

For palewi.re's own public pages, use the separate
[site archive workflow](site-archive.md). It includes same-site documentation
and HTML slide decks, keeps a durable manifest on `site-archive-data`, and
requests missing Wayback captures. Its coverage report is separate from the
external-content inventory below, and it is not a replacement for media backup.

The preservation inventory is a local, network-free view of two separate
systems:

| Material | Source of truth | Preservation method | Storage boundary |
| --- | --- | --- | --- |
| Public clip pages | `coltrane/content/clips.yaml` | Wayback snapshot or recorded exemption | Public Internet Archive URL |
| Playable audio and video | External `manifest.json` | Local downloaded file with SHA-256 checksum | A user-chosen directory outside this repository |
| Private replica | `manifest.json` plus verified local archive | Private R2 copy of verified local media | Private R2 bucket |

The report does not fetch pages, download media, recompute checksums, upload
files, or write a database. It never copies media or its manifest into Git.
It joins records only when their source URLs match. A source URL can have both
the `webpage` and `media:*` classifications; in that case, it needs both
applicable methods.

## Running the report

```bash
# Shows all current media as untracked because no external manifest is joined.
make preservation-inventory

# Joins the selected external manifest. The root must be outside this repo.
ARCHIVE_ROOT=/absolute/path/outside/the/repo make preservation-inventory

# Write stable JSON for another local maintenance tool.
uv run python -m scripts.preservation_inventory \
  --archive-root /absolute/path/outside/the/repo \
  --json-output /tmp/preservation-inventory.json
```

The JSON format is versioned (`version: 1`) and deterministic: sources,
origins, classifications, status summaries, and gap records are sorted. It
contains no run timestamp or machine-specific archive path. Consumers should
use the explicit `status`, `verification_status`, and `gaps` fields instead
of parsing terminal output. The terminal shows the first 20 gap details by
default; use `--max-gaps 0` for a summary-only run.

## New-content review

```bash
make preservation-review
```

This is the pull-request check for newly added or changed external content.
It generates the unified inventory in a temporary file and compares its
current-source gaps with `preservation-review-baseline.json`. It never needs
an archive root or credentials, and never contacts Wayback, downloads media,
or uploads to R2.

The baseline contains only source URL, gap code, and a recorded reason. The
current entries are the documented historical media recovery work in issue
#396. A newly introduced gap fails with the exact `clip`, `talk`, or `post`
location and an appropriate next action:

- A clip needs `make archive-clips`, followed by `make check-clip-archives`.
  A truthful `archive_exemption` in `clips.yaml` is already valid and creates
  no gap. A missing Wayback record can never be accepted in the baseline.
- Playable media needs a permitted local backup, checksum verification, and
  private R2 replication. The command prints the exact local commands.
- A DRM-protected, private, login-required, or otherwise inaccessible media
  source may be accepted only by adding its exact URL and gap code to the
  baseline with a specific reason that says why access controls cannot be
  used. This is a review record, not permission to bypass the restriction.

Remove a baseline entry when the current source is no longer present or its
gap has been resolved. The command reports stale entries so the baseline
remains an intentional list rather than a permanent suppression.

## Status vocabulary

Wayback status applies only to a clip URL:

| Status | Meaning |
| --- | --- |
| `snapshot` | `archive_url` points to a Wayback snapshot. |
| `exempt` | `archive_exemption` documents why Wayback cannot preserve the page. |
| `missing` | No snapshot or exemption is recorded. |
| `not-applicable` | The source is not a clip page. |

Local-media status applies only to playable media:

| Status | Meaning |
| --- | --- |
| `untracked` | The current source has no entry in the joined manifest, or no root was supplied. |
| `pending` | The manifest has not recorded a completed backup. |
| `success` | A download completed and the manifest records its checksum and size. |
| `failed` | The last permitted download attempt failed; inspect `error`. |
| `skipped` | The manifest records that the source was intentionally skipped. Resolve it explicitly. |
| `invalid` | The manifest has an unsupported status value. |
| `not-applicable` | The source is not playable media. |

`verification_status` is `verified` only after the offline checksum command
has recorded a successful verification. A `success` item without that record
is `not-verified` and is listed as a gap.

## Exemptions and gaps

Use a Wayback exemption only when the page cannot be captured, such as a
publisher robots policy. Keep the explanation brief and specific. An
exemption is not a substitute for a missing snapshot, and it does not apply
to a playable media source.

The report names gaps with stable codes. `wayback-missing` needs a snapshot or
a specific exemption. `local-media-untracked`, `local-media-pending`,
`local-media-failed`, and `local-media-skipped` need a local maintenance
decision. `local-media-not-verified` needs the checksum command. An archived
media source that is no longer referenced remains in the manifest and is
reported as historical; do not delete it solely because it no longer appears
on the site.

## Safe maintenance cadence

1. After adding or changing a clip URL, run `make archive-clips`, then
   `make check-clip-archives` and `make preservation-review`.
2. After adding playable media to a talk or post, run
   `make preservation-review`. Follow its source-specific action or record a
   specific access-control reason in the baseline.
3. Before a media backup session, review `make media-archive-inventory` and
   the combined report.
4. Back up only permitted public sources to a chosen external root with
   `ARCHIVE_ROOT=/path/outside/repo make media-archive-backup`.
5. After each backup session, and at least quarterly for long-lived storage,
   run `uv run python -m scripts.media_archive verify --archive-root /path/outside/repo`.
6. Replicate only verified local media with
   `ARCHIVE_ROOT=/path/outside/repo make media-archive-r2-sync`, then confirm
   it with `make media-archive-r2-verify`.

The R2 replica may copy only a verified local-media record and its checksum
metadata. It is intentionally manual: this project does not configure
credentials, schedules, or public media serving.

## Recovery boundaries

Wayback snapshots are external public references. If a snapshot disappears,
rerun the clip archive workflow or record a specific, truthful exemption; a
local media file is not a replacement for a page snapshot.

The external media manifest and files are the recovery source for local
media. Restore a selected verified file from private R2 with
`make media-archive-r2-recover`, or from another durable copy, then run the
offline verification command. Do not recreate a manifest entry by guessing
its checksum or download around access controls. Sources that require DRM,
login, paywalls, or other access controls remain failed or skipped with their
recorded reason.
