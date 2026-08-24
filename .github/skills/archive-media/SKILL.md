---
name: archive-media
description: Preservation-only backup of audio/video referenced by coltrane/content/talks.yaml and coltrane/content/posts/. Use whenever running, auditing, or troubleshooting a durable local media backup so embeds are not lost if they disappear from the web.
---

# Archive audio/video media

This tooling discovers every playable audio/video source referenced by talks
and blog posts, then uses `yt-dlp` to download a durable copy into a
directory **outside** this Git repository. Nothing is ever committed, and
nothing is ever written under a repo static path. See issue #176.

## Safety rules (read first)

- Binaries only ever go to `--archive-root` (or `MEDIA_ARCHIVE_PATH`), a
  directory you choose **outside** this repository. The CLI refuses any path
  inside the repo.
- This is preservation only. It never bypasses DRM, private access, login
  requirements, paywalls, or any other access control. If yt-dlp cannot fetch
  something without doing that, treat the failure as expected and move on.
- `ffmpeg` is only required for sources that need muxing (YouTube, Vimeo, or
  an unrecognized host). Direct file links and SoundCloud usually don't need
  it. `ffmpeg` is never installed by `make bootstrap`; install it yourself
  (e.g. `brew install ffmpeg`) only when you are about to back up those kinds.
- Every run is idempotent and resumable. Re-running `backup` skips anything
  already marked `success` in the manifest, and the manifest is rewritten
  after every single item, so an interrupted run loses no progress.

## Commands

All commands live under `python -m scripts.media_archive` (or the equivalent
`make` targets).

### 1. Inventory (dry run, no network, no archive root needed)

```bash
make media-archive-inventory
```

Lists every discovered candidate, deduplicated by URL, with a breakdown by
talk/post origin and by kind (`direct`, `youtube`, `vimeo`, `soundcloud`,
`unknown`). Add `--json-output path.json` for machine-readable output. This
step never touches the network or writes any media.

### 2. Backup (downloads to your chosen archive root)

```bash
ARCHIVE_ROOT=/absolute/path/outside/the/repo make media-archive-backup
```

or directly:

```bash
uv run python -m scripts.media_archive backup --archive-root /absolute/path/outside/the/repo
```

Useful flags:

- `--limit N` — process at most N candidates (good for a first careful run).
- `--delay SECONDS` — pause between downloads (default 1s); be polite to
  hosts.
- `--force` — re-download and overwrite entries already marked `success`.
- `--no-retry-failed` — skip candidates that failed on a previous run instead
  of retrying them (retrying is the default).

The command warns (but does not stop) if `ffmpeg` is missing and pending
candidates need it. It exits non-zero if any candidate fails, so CI/automation
can detect problems, but every attempted item's error is always written to the
manifest — nothing fails silently.

### 3. Verify (offline, recomputes checksums)

```bash
uv run python -m scripts.media_archive verify --archive-root /absolute/path/outside/the/repo
```

Recomputes the SHA-256 and size of every file marked `success` and reports
`MISSING` or `MISMATCH` for any problem. Never touches the network.

## The manifest

`<archive-root>/manifest.json` is the single source of truth. It is always
written atomically (temp file + rename), so a crash never leaves a corrupt
manifest. Each entry records: source URL, every occurrence (talk/post that
referenced it), extractor and media identity, status (`pending` / `success` /
`failed` / `skipped`), output filename, size, SHA-256 checksum, the yt-dlp
`.info.json` sidecar path when available, timestamps, and — on failure — the
exact error message. Entries are never deleted, even if content changes
later, so the manifest is a durable history.

## Typical safe workflow

1. `make media-archive-inventory` to see what would be backed up.
2. Pick (or create) a real external archive directory, e.g. an attached
   drive or a directory outside any repo.
3. `ARCHIVE_ROOT=/path/to/archive make media-archive-backup` — start small
   with `--limit` if you want to sanity check the first few downloads.
4. Re-run the same command any time; it only attempts what is still pending
   or previously failed.
5. `uv run python -m scripts.media_archive verify --archive-root /path/to/archive`
   periodically to confirm nothing has bit-rotted or gone missing.

## Do not

- Do not point `--archive-root` / `MEDIA_ARCHIVE_PATH` at anything inside
  this repository — the CLI refuses this on purpose.
- Do not add Actions schedules, cloud storage configuration (R2/S3), or
  Django static-file storage for this tooling. It is a local/manual
  maintenance script, not a deployed feature.
- Do not close issue #176 after adding this tooling. Close it only once a
  real, durable backup run has actually been completed against a real
  archive location.
