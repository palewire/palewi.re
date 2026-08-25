# Preservation policy and runbook

## Purpose and boundaries

The preservation inventory is a local, network-free view of two separate
systems:

| Material | Source of truth | Preservation method | Storage boundary |
| --- | --- | --- | --- |
| Public clip pages | `coltrane/content/clips.yaml` | Wayback snapshot or recorded exemption | Public Internet Archive URL |
| Playable audio and video | External `manifest.json` | Local downloaded file with SHA-256 checksum | A user-chosen directory outside this repository |
| Future replica | Future R2 process | Private copy of verified local media | Not implemented by this policy |

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

1. After changing a clip URL, run `make archive-clips`, then
   `make check-clip-archives`.
2. Before a media backup session, review `make media-archive-inventory` and
   the combined report.
3. Back up only permitted public sources to a chosen external root with
   `ARCHIVE_ROOT=/path/outside/repo make media-archive-backup`.
4. After each backup session, and at least quarterly for long-lived storage,
   run `uv run python -m scripts.media_archive verify --archive-root /path/outside/repo`.
5. Re-run the combined report and keep its JSON with local maintenance
   records if another system needs it.

The future R2 replica may copy only a verified local-media record and its
checksum metadata. It is intentionally outside this workflow: this project
does not configure R2 credentials, uploads, replication schedules, or public
media serving.

## Recovery boundaries

Wayback snapshots are external public references. If a snapshot disappears,
rerun the clip archive workflow or record a specific, truthful exemption; a
local media file is not a replacement for a page snapshot.

The external media manifest and files are the recovery source for local
media. Restore a missing or checksum-mismatched file from a separate durable
copy, then run the offline verification command. Do not recreate a manifest
entry by guessing its checksum or download around access controls. Sources
that require DRM, login, paywalls, or other access controls remain failed or
skipped with their recorded reason.
