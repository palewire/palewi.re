---
name: archive-clips
description: Archive URLs added to or changed in coltrane/content/clips.yaml with the Wayback Machine. Use whenever adding, editing, auditing, or repairing clip links or their archive metadata.
---

# Archive clip URLs

Every clip URL should have a durable Wayback snapshot. The repository command
checks for an existing snapshot before requesting a new authenticated capture.

## When adding or changing a clip

1. Edit `coltrane/content/clips.yaml`.
2. Run `make archive-clips`.
3. Review the added `archive_url` or `archive_exemption`.
4. Run `make check-clip-archives`.
5. Run `make check`.

The capture command saves after every URL, so it is safe to rerun after a
network error. Use the Python command directly with `--limit` for a controlled
batch:

```bash
uv run python -m scripts.archive_clips archive --limit 10
```

Creating a new snapshot requires `SAVEPAGENOW_ACCESS_KEY` and
`SAVEPAGENOW_SECRET_KEY`. Never print or commit either value. Existing
snapshots can be found without credentials.

Only use `archive_exemption` when Wayback cannot capture the page. Keep the
reason short and specific. Do not add an exemption merely to bypass the check.
