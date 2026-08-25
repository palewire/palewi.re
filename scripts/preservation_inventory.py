"""Build a network-free report of the site's preservation coverage."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import click

from coltrane.content_loaders import Clip, ContentError, load_clips, load_posts, load_talks
from scripts.media_archive import manifest as manifest_mod
from scripts.media_archive.cli import REPO_ROOT, _resolve_archive_root
from scripts.media_archive.discovery import MediaCandidate, discover_candidates

INVENTORY_VERSION = 1
CLIPS_PATH = REPO_ROOT / "coltrane" / "content" / "clips.yaml"
TALKS_PATH = REPO_ROOT / "coltrane" / "content" / "talks.yaml"
POSTS_PATH = REPO_ROOT / "coltrane" / "content" / "posts"

WAYBACK_SNAPSHOT = "snapshot"
WAYBACK_EXEMPT = "exempt"
WAYBACK_MISSING = "missing"
WAYBACK_NOT_APPLICABLE = "not-applicable"

LOCAL_UNTRACKED = "untracked"
LOCAL_NOT_APPLICABLE = "not-applicable"
LOCAL_INVALID = "invalid"
VERIFICATION_VERIFIED = "verified"
VERIFICATION_NOT_VERIFIED = "not-verified"
VERIFICATION_NOT_APPLICABLE = "not-applicable"

MANIFEST_STATUSES = frozenset(
    {
        manifest_mod.STATUS_PENDING,
        manifest_mod.STATUS_SUCCESS,
        manifest_mod.STATUS_FAILED,
        manifest_mod.STATUS_SKIPPED,
    }
)


@dataclass
class InventorySource:
    """One URL and all preservation records that apply to it."""

    source_url: str
    classifications: set[str] = field(default_factory=set)
    origins: list[dict[str, str]] = field(default_factory=list)
    has_current_reference: bool = False
    wayback: dict[str, str | None] = field(
        default_factory=lambda: {
            "status": WAYBACK_NOT_APPLICABLE,
            "archive_url": None,
            "archive_exemption": None,
        }
    )
    local_media: dict[str, str | int | None] = field(
        default_factory=lambda: {
            "status": LOCAL_NOT_APPLICABLE,
            "manifest_status": None,
            "kind": None,
            "verification_status": VERIFICATION_NOT_APPLICABLE,
            "attempts": None,
            "last_attempt_at": None,
            "last_verified_at": None,
            "output_filename": None,
            "size_bytes": None,
            "sha256": None,
            "error": None,
        }
    )

    def add_origins(self, origins: list[dict[str, str]]) -> None:
        """Add unique origins while preserving a deterministic output order."""
        self.origins.extend(origin for origin in origins if origin not in self.origins)

    def to_dict(self) -> dict[str, Any]:
        """Return the stable JSON representation for this source."""
        methods: list[str] = []
        if self.wayback["status"] != WAYBACK_NOT_APPLICABLE:
            methods.append("wayback")
        if self.local_media["status"] != LOCAL_NOT_APPLICABLE:
            methods.append("local-media")

        result = {
            "source_url": self.source_url,
            "classifications": sorted(self.classifications),
            "current_reference": self.has_current_reference,
            "origins": sorted(
                self.origins,
                key=lambda origin: (
                    origin.get("origin_type", ""),
                    origin.get("origin_id", ""),
                    origin.get("location", ""),
                    origin.get("raw_url", ""),
                ),
            ),
            "preservation_methods": methods,
            "wayback": self.wayback,
            "local_media": self.local_media,
        }
        result["gaps"] = source_gaps(result)
        return result


def clip_origin(clip: Clip) -> dict[str, str]:
    """Return a location record for a clip source URL."""
    return {
        "origin_type": "clip",
        "origin_id": clip.title,
        "location": "clips.yaml:url",
        "raw_url": clip.url,
    }


def candidate_origins(candidate: MediaCandidate) -> list[dict[str, str]]:
    """Return content locations for a discovered media candidate."""
    return [
        {
            "origin_type": occurrence.origin_type,
            "origin_id": occurrence.origin_id,
            "location": occurrence.location,
            "raw_url": occurrence.raw_url,
        }
        for occurrence in candidate.occurrences
    ]


def manifest_origins(entry: manifest_mod.ManifestEntry) -> list[dict[str, str]]:
    """Return the durable occurrence history stored by the media manifest."""
    return [
        {
            "origin_type": origin.get("origin_type", "unknown"),
            "origin_id": origin.get("origin_id", "unknown"),
            "location": origin.get("location", "unknown"),
            "raw_url": origin.get("raw_url", entry.source_url),
        }
        for origin in entry.occurrences
    ]


def local_media_record(entry: manifest_mod.ManifestEntry | None) -> dict[str, str | int | None]:
    """Return media state without reading media files or contacting any service."""
    if entry is None:
        return {
            "status": LOCAL_UNTRACKED,
            "manifest_status": None,
            "kind": None,
            "verification_status": VERIFICATION_NOT_APPLICABLE,
            "attempts": None,
            "last_attempt_at": None,
            "last_verified_at": None,
            "output_filename": None,
            "size_bytes": None,
            "sha256": None,
            "error": None,
        }

    status = entry.status if entry.status in MANIFEST_STATUSES else LOCAL_INVALID
    last_verified_at = entry.last_verified_at
    verification_status = VERIFICATION_NOT_APPLICABLE
    if status == manifest_mod.STATUS_SUCCESS:
        verification_status = VERIFICATION_VERIFIED if last_verified_at else VERIFICATION_NOT_VERIFIED
    return {
        "status": status,
        "manifest_status": entry.status,
        "kind": entry.kind,
        "verification_status": verification_status,
        "attempts": entry.attempts,
        "last_attempt_at": entry.updated_at if entry.attempts else None,
        "last_verified_at": last_verified_at,
        "output_filename": entry.output_filename,
        "size_bytes": entry.size_bytes,
        "sha256": entry.sha256,
        "error": entry.error,
    }


def source_gaps(source: dict[str, Any]) -> list[dict[str, str]]:
    """List action-specific preservation gaps without turning status into policy."""
    gaps: list[dict[str, str]] = []
    wayback_status = source["wayback"]["status"]
    if wayback_status == WAYBACK_MISSING:
        gaps.append(
            {
                "code": "wayback-missing",
                "message": "A clip source needs a Wayback snapshot or a specific exemption.",
            }
        )

    media = source["local_media"]
    media_status = media["status"]
    if media_status == LOCAL_UNTRACKED:
        gaps.append(
            {
                "code": "local-media-untracked",
                "message": "No entry for this current media source was found in the external manifest.",
            }
        )
    elif media_status == manifest_mod.STATUS_PENDING:
        gaps.append(
            {
                "code": "local-media-pending",
                "message": "The external manifest has not recorded a completed local-media backup.",
            }
        )
    elif media_status == manifest_mod.STATUS_FAILED:
        detail = f" Last error: {media['error']}" if media["error"] else ""
        gaps.append(
            {
                "code": "local-media-failed",
                "message": f"The last local-media backup attempt failed.{detail}",
            }
        )
    elif media_status == manifest_mod.STATUS_SKIPPED:
        gaps.append(
            {
                "code": "local-media-skipped",
                "message": "The external manifest marks this local-media source as skipped.",
            }
        )
    elif media_status == LOCAL_INVALID:
        gaps.append(
            {
                "code": "local-media-invalid-status",
                "message": f"The external manifest has an unsupported status: {media['manifest_status']}.",
            }
        )
    elif media_status == manifest_mod.STATUS_SUCCESS and media["verification_status"] == VERIFICATION_NOT_VERIFIED:
        gaps.append(
            {
                "code": "local-media-not-verified",
                "message": "A downloaded file has not yet passed a recorded offline checksum verification.",
            }
        )
    return gaps


def build_inventory(
    clips: list[Clip],
    candidates: list[MediaCandidate],
    manifest: manifest_mod.Manifest | None,
    *,
    archive_root_provided: bool,
    manifest_found: bool,
) -> dict[str, Any]:
    """Join current site sources with an optional external media manifest."""
    sources: dict[str, InventorySource] = {}

    def get_source(url: str) -> InventorySource:
        if url not in sources:
            sources[url] = InventorySource(source_url=url)
        return sources[url]

    for clip in clips:
        source = get_source(clip.url)
        source.has_current_reference = True
        source.classifications.add("webpage")
        source.add_origins([clip_origin(clip)])
        source.wayback = {
            "status": WAYBACK_SNAPSHOT
            if clip.archive_url
            else WAYBACK_EXEMPT
            if clip.archive_exemption
            else WAYBACK_MISSING,
            "archive_url": clip.archive_url or None,
            "archive_exemption": clip.archive_exemption or None,
        }

    for candidate in candidates:
        source = get_source(candidate.url)
        source.has_current_reference = True
        source.classifications.add(f"media:{candidate.kind}")
        source.add_origins(candidate_origins(candidate))
        entry = manifest.entries.get(candidate.url) if manifest is not None else None
        source.local_media = local_media_record(entry)
        if entry is not None:
            source.add_origins(manifest_origins(entry))

    if manifest is not None:
        for url, entry in manifest.entries.items():
            source = get_source(url)
            source.classifications.add(f"media:{entry.kind}")
            source.add_origins(manifest_origins(entry))
            if source.local_media["status"] == LOCAL_NOT_APPLICABLE:
                source.local_media = local_media_record(entry)

    serialized_sources = [sources[url].to_dict() for url in sorted(sources)]
    wayback_statuses = Counter(
        source["wayback"]["status"]
        for source in serialized_sources
        if source["wayback"]["status"] != WAYBACK_NOT_APPLICABLE
    )
    media_statuses = Counter(
        source["local_media"]["status"]
        for source in serialized_sources
        if source["local_media"]["status"] != LOCAL_NOT_APPLICABLE
    )
    gap_count = sum(len(source["gaps"]) for source in serialized_sources)
    return {
        "version": INVENTORY_VERSION,
        "media_manifest": {
            "archive_root_provided": archive_root_provided,
            "manifest_found": manifest_found,
        },
        "sources": serialized_sources,
        "summary": {
            "source_count": len(serialized_sources),
            "current_source_count": sum(source["current_reference"] for source in serialized_sources),
            "historical_media_source_count": sum(not source["current_reference"] for source in serialized_sources),
            "wayback_statuses": dict(sorted(wayback_statuses.items())),
            "local_media_statuses": dict(sorted(media_statuses.items())),
            "gap_count": gap_count,
        },
    }


def load_inventory(
    clips_path: Path,
    talks_path: Path,
    posts_path: Path,
    archive_root: Path | None,
) -> dict[str, Any]:
    """Load content and optional manifest without performing network or file checks."""
    try:
        clips = load_clips(clips_path)
        candidates = discover_candidates(load_talks(talks_path), load_posts(posts_path))
    except ContentError as error:
        raise click.ClickException(str(error)) from error

    if archive_root is None:
        return build_inventory(clips, candidates, None, archive_root_provided=False, manifest_found=False)

    resolved_root = _resolve_archive_root(archive_root)
    manifest_file = manifest_mod.manifest_path(resolved_root)
    try:
        manifest = manifest_mod.load_manifest(resolved_root)
    except manifest_mod.ManifestError as error:
        raise click.ClickException(str(error)) from error
    return build_inventory(
        clips,
        candidates,
        manifest,
        archive_root_provided=True,
        manifest_found=manifest_file.exists(),
    )


def print_inventory(inventory: dict[str, Any], max_gaps: int) -> None:
    """Render a concise human-readable report from the stable JSON data."""
    summary = inventory["summary"]
    click.echo(
        f"Preservation inventory: {summary['source_count']} source URL(s), "
        f"{summary['current_source_count']} current, {summary['gap_count']} gap(s)."
    )
    click.echo(f"  Wayback: {format_status_counts(summary['wayback_statuses'])}")
    click.echo(f"  Local media: {format_status_counts(summary['local_media_statuses'])}")
    displayed_gaps = 0
    for source in inventory["sources"]:
        for gap in source["gaps"]:
            if max_gaps and displayed_gaps == max_gaps:
                remaining = summary["gap_count"] - displayed_gaps
                click.echo(f"... {remaining} additional gap(s) are available in the JSON report.")
                return
            if max_gaps == 0:
                continue
            click.echo(f"{gap['code'].upper()}  {source['source_url']}  {gap['message']}")
            displayed_gaps += 1


def format_status_counts(counts: dict[str, int]) -> str:
    """Format sorted status counts for terminal output."""
    return ", ".join(f"{status}={count}" for status, count in sorted(counts.items())) or "none"


@click.command()
@click.option(
    "--clips-path", type=click.Path(path_type=Path, exists=True, dir_okay=False), default=CLIPS_PATH, show_default=True
)
@click.option(
    "--talks-path", type=click.Path(path_type=Path, exists=True, dir_okay=False), default=TALKS_PATH, show_default=True
)
@click.option(
    "--posts-path", type=click.Path(path_type=Path, exists=True, file_okay=False), default=POSTS_PATH, show_default=True
)
@click.option(
    "--archive-root",
    type=click.Path(path_type=Path, file_okay=False),
    envvar="MEDIA_ARCHIVE_PATH",
    default=None,
    help="External media archive root to join through its manifest.json file.",
)
@click.option(
    "--json-output",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Write the stable JSON report to this path.",
)
@click.option(
    "--max-gaps",
    type=click.IntRange(min=0),
    default=20,
    show_default=True,
    help="Maximum number of gap details to show in the terminal.",
)
def cli(
    clips_path: Path,
    talks_path: Path,
    posts_path: Path,
    archive_root: Path | None,
    json_output: Path | None,
    max_gaps: int,
) -> None:
    """Report page and media preservation state without network access."""
    inventory = load_inventory(clips_path, talks_path, posts_path, archive_root)
    print_inventory(inventory, max_gaps)
    if json_output is not None:
        json_output.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        click.echo(f"Wrote JSON inventory to {json_output}")


if __name__ == "__main__":
    cli()
