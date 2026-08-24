"""Atomic, durable manifest tracking every media archive attempt.

The manifest is the single source of truth for idempotent, resumable
downloads. It lives inside the archive root (never inside the Git
repository) as ``manifest.json`` and is always rewritten atomically: a
temporary file is written and then renamed over the target so a crash or
interrupted process can never leave a half-written manifest behind.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.media_archive.discovery import MediaCandidate, MediaOccurrence

MANIFEST_VERSION = 1
MANIFEST_FILENAME = "manifest.json"

STATUS_PENDING = "pending"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"

_CHECKSUM_CHUNK_SIZE = 1024 * 1024


def current_timestamp() -> str:
    """Return the current UTC time as an ISO 8601 string.

    This uses the standard library directly (not ``django.utils.timezone``)
    so the archive CLI works standalone, without ``DJANGO_SETTINGS_MODULE``
    configured, exactly like the rest of ``scripts/``.
    """
    return datetime.now(UTC).isoformat()


@dataclass
class ManifestEntry:
    """One tracked media source and the outcome of the last attempt to back it up."""

    source_url: str
    kind: str
    occurrences: list[dict[str, str]]
    status: str = STATUS_PENDING
    extractor: str | None = None
    media_id: str | None = None
    output_filename: str | None = None
    size_bytes: int | None = None
    sha256: str | None = None
    info_json_path: str | None = None
    attempts: int = 0
    error: str | None = None
    created_at: str = field(default_factory=current_timestamp)
    updated_at: str = field(default_factory=current_timestamp)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ManifestEntry:
        """Rebuild an entry from its JSON-serializable representation."""
        known_fields = {f for f in cls.__dataclass_fields__}
        return cls(**{key: value for key, value in data.items() if key in known_fields})


@dataclass
class Manifest:
    """The full set of tracked media entries, keyed by source URL."""

    entries: dict[str, ManifestEntry] = field(default_factory=dict)
    version: int = MANIFEST_VERSION
    updated_at: str = field(default_factory=current_timestamp)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation with sorted keys for stable diffs."""
        return {
            "version": self.version,
            "updated_at": self.updated_at,
            "entries": {url: self.entries[url].to_dict() for url in sorted(self.entries)},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Manifest:
        """Rebuild a manifest from its JSON-serializable representation."""
        entries = {url: ManifestEntry.from_dict(entry) for url, entry in data.get("entries", {}).items()}
        return cls(
            entries=entries,
            version=data.get("version", MANIFEST_VERSION),
            updated_at=data.get("updated_at", current_timestamp()),
        )


class ManifestError(RuntimeError):
    """Raised when a manifest file on disk is invalid."""


def manifest_path(archive_root: Path) -> Path:
    """Return the manifest path inside an archive root."""
    return archive_root / MANIFEST_FILENAME


def load_manifest(archive_root: Path) -> Manifest:
    """Load the manifest from an archive root, or return an empty one."""
    path = manifest_path(archive_root)
    if not path.exists():
        return Manifest()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ManifestError(f"{path}: manifest is not valid JSON") from error
    if not isinstance(raw, dict):
        raise ManifestError(f"{path}: manifest must be a JSON object")
    return Manifest.from_dict(raw)


def write_manifest(archive_root: Path, manifest: Manifest) -> None:
    """Atomically write the manifest, updating its top-level timestamp."""
    archive_root.mkdir(parents=True, exist_ok=True)
    manifest.updated_at = current_timestamp()
    path = manifest_path(archive_root)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    temporary_path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=False) + "\n", encoding="utf-8")
    temporary_path.replace(path)


def sha256_file(path: Path) -> str:
    """Compute the SHA-256 checksum of a file, reading it in fixed-size chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHECKSUM_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def occurrence_to_dict(occurrence: MediaOccurrence) -> dict[str, str]:
    """Serialize an occurrence for storage in the manifest."""
    return {
        "origin_type": occurrence.origin_type,
        "origin_id": occurrence.origin_id,
        "location": occurrence.location,
        "raw_url": occurrence.raw_url,
    }


def sync_candidates(manifest: Manifest, candidates: list[MediaCandidate]) -> Manifest:
    """Ensure every discovered candidate has a manifest entry.

    Existing entries keep their download status and history; only their
    ``kind`` and ``occurrences`` are refreshed to match the latest discovery
    pass. New candidates are added as ``pending``. Nothing is ever deleted,
    so the manifest retains a durable record even if content changes later.
    """
    for candidate in candidates:
        occurrence_dicts = [occurrence_to_dict(occurrence) for occurrence in candidate.occurrences]
        existing = manifest.entries.get(candidate.url)
        if existing is None:
            manifest.entries[candidate.url] = ManifestEntry(
                source_url=candidate.url,
                kind=candidate.kind,
                occurrences=occurrence_dicts,
            )
        else:
            existing.kind = candidate.kind
            existing.occurrences = occurrence_dicts
    return manifest
