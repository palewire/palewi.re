"""Click commands for the preservation-only media archive.

Commands:

* ``inventory`` - discover candidates without downloading anything (dry run).
* ``backup`` - download pending/failed candidates into ``--archive-root``.
* ``verify`` - recompute checksums of already-downloaded files, offline.
* ``r2-sync`` - replicate verified local media to a private R2 bucket.
* ``r2-verify`` - compare local archive checksums against private R2 metadata.
* ``r2-recover`` - restore one selected media file from private R2.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import click

from coltrane.content_loaders import ContentError, load_posts, load_talks
from scripts.media_archive import manifest as manifest_mod
from scripts.media_archive import r2
from scripts.media_archive.discovery import MediaCandidate, discover_candidates
from scripts.media_archive.downloader import DownloadError, download_candidate, ffmpeg_available

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_candidates(talks_path: Path | None, posts_path: Path | None) -> list[MediaCandidate]:
    """Load talks and posts, then discover media candidates."""
    try:
        talks = load_talks(talks_path) if talks_path else load_talks()
        posts = load_posts(posts_path) if posts_path else load_posts()
    except ContentError as error:
        raise click.ClickException(str(error)) from error
    return discover_candidates(talks, posts)


def _resolve_archive_root(value: Path | None) -> Path:
    """Validate and normalize a user-selected archive root, outside the repository."""
    if value is None:
        raise click.ClickException(
            "An archive root is required. Pass --archive-root or set the MEDIA_ARCHIVE_PATH "
            "environment variable to a directory outside this repository."
        )
    resolved = value.expanduser().resolve()
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        raise click.ClickException(
            f"Refusing to store media under the repository at {REPO_ROOT}. Choose an external --archive-root."
        )
    return resolved


def _talks_path_option() -> Any:
    return click.option(
        "--talks-path",
        type=click.Path(path_type=Path, exists=True, dir_okay=False),
        default=None,
        help="Override the talks YAML path (defaults to coltrane/content/talks.yaml).",
    )


def _posts_path_option() -> Any:
    return click.option(
        "--posts-path",
        type=click.Path(path_type=Path, exists=True, file_okay=False),
        default=None,
        help="Override the posts directory (defaults to coltrane/content/posts).",
    )


def _archive_root_option() -> Any:
    return click.option(
        "--archive-root",
        "archive_root",
        type=click.Path(path_type=Path, file_okay=False),
        envvar="MEDIA_ARCHIVE_PATH",
        default=None,
        help="Directory outside the repository where media and the manifest are stored. "
        "Can also be set with the MEDIA_ARCHIVE_PATH environment variable.",
    )


def _r2_bucket_option() -> Any:
    return click.option(
        "--bucket",
        type=str,
        default=r2.DEFAULT_BUCKET,
        show_default=True,
        envvar="MEDIA_ARCHIVE_R2_BUCKET",
        help="Private R2 bucket containing this archive replica.",
    )


@click.group()
def cli() -> None:
    """Discover and preserve playable audio/video sources referenced by the site."""


@cli.command()
@_talks_path_option()
@_posts_path_option()
@click.option(
    "--json-output",
    "json_output_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Write the discovered candidates as JSON to this path.",
)
def inventory(talks_path: Path | None, posts_path: Path | None, json_output_path: Path | None) -> None:
    """List discovered media candidates without downloading anything."""
    candidates = _load_candidates(talks_path, posts_path)

    talk_count = sum(1 for candidate in candidates if any(o.origin_type == "talk" for o in candidate.occurrences))
    post_count = sum(1 for candidate in candidates if any(o.origin_type == "post" for o in candidate.occurrences))
    by_kind: dict[str, int] = {}
    for candidate in candidates:
        by_kind[candidate.kind] = by_kind.get(candidate.kind, 0) + 1
    total_occurrences = sum(len(candidate.occurrences) for candidate in candidates)

    click.echo(f"Discovered {len(candidates)} unique media candidate(s) ({total_occurrences} occurrence(s)).")
    click.echo(f"  Referenced by talks: {talk_count}")
    click.echo(f"  Referenced by posts: {post_count}")
    for kind in sorted(by_kind):
        click.echo(f"  {kind}: {by_kind[kind]}")

    if json_output_path is not None:
        payload = [
            {
                "url": candidate.url,
                "kind": candidate.kind,
                "occurrences": [
                    {
                        "origin_type": occurrence.origin_type,
                        "origin_id": occurrence.origin_id,
                        "location": occurrence.location,
                        "raw_url": occurrence.raw_url,
                    }
                    for occurrence in candidate.occurrences
                ],
            }
            for candidate in candidates
        ]
        json_output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        click.echo(f"Wrote candidate JSON to {json_output_path}")


@cli.command()
@_archive_root_option()
@_talks_path_option()
@_posts_path_option()
@click.option("--limit", type=click.IntRange(min=1), default=None, help="Process at most this many candidates.")
@click.option(
    "--delay", type=click.FloatRange(min=0), default=1.0, show_default=True, help="Seconds between downloads."
)
@click.option(
    "--force/--no-force",
    default=False,
    help="Re-download and overwrite entries already marked successful.",
)
@click.option(
    "--retry-failed/--no-retry-failed",
    default=True,
    show_default=True,
    help="Retry candidates that previously failed.",
)
def backup(
    archive_root: Path | None,
    talks_path: Path | None,
    posts_path: Path | None,
    limit: int | None,
    delay: float,
    force: bool,
    retry_failed: bool,
) -> None:
    """Download pending (and, by default, previously failed) media into --archive-root."""
    resolved_root = _resolve_archive_root(archive_root)
    candidates = _load_candidates(talks_path, posts_path)
    manifest = manifest_mod.load_manifest(resolved_root)
    manifest = manifest_mod.sync_candidates(manifest, candidates)
    manifest_mod.write_manifest(resolved_root, manifest)

    def needs_attempt(entry: manifest_mod.ManifestEntry) -> bool:
        if force:
            return True
        if entry.status == manifest_mod.STATUS_SUCCESS:
            return False
        if entry.status == manifest_mod.STATUS_FAILED and not retry_failed:
            return False
        return True

    pending_urls = [candidate.url for candidate in candidates if needs_attempt(manifest.entries[candidate.url])]
    if limit is not None:
        pending_urls = pending_urls[:limit]

    if not pending_urls:
        click.echo("Nothing to back up. Every candidate is already marked successful.")
        return

    if any(manifest.entries[url].kind != "direct" for url in pending_urls) and not ffmpeg_available():
        click.echo(
            "Warning: ffmpeg was not found on PATH. Downloads that require merging separate "
            "audio/video streams (YouTube, Vimeo) will fail until ffmpeg is installed.",
            err=True,
        )

    successes = 0
    failures = 0
    for index, url in enumerate(pending_urls, start=1):
        entry = manifest.entries[url]
        click.echo(f"[{index}/{len(pending_urls)}] {entry.kind}: {url}")
        entry.attempts += 1
        outcome = None
        try:
            outcome = download_candidate(url, entry.kind, resolved_root)
        except DownloadError as error:
            entry.status = manifest_mod.STATUS_FAILED
            entry.error = str(error)
            click.echo(f"  failed: {error}")
            failures += 1
        if outcome is not None:
            if outcome.status == "success":
                entry.status = manifest_mod.STATUS_SUCCESS
                entry.extractor = outcome.extractor
                entry.media_id = outcome.media_id
                entry.output_filename = outcome.output_filename
                entry.size_bytes = outcome.size_bytes
                assert outcome.output_filename is not None
                entry.sha256 = manifest_mod.sha256_file(resolved_root / outcome.output_filename)
                entry.info_json_path = outcome.info_json_path
                entry.error = None
                click.echo(f"  success: {outcome.output_filename} ({outcome.size_bytes} bytes)")
                successes += 1
            else:
                entry.status = manifest_mod.STATUS_FAILED
                entry.error = outcome.error
                click.echo(f"  failed: {outcome.error}")
                failures += 1
        entry.updated_at = manifest_mod.current_timestamp()
        # Write after every item so progress survives an interruption.
        manifest_mod.write_manifest(resolved_root, manifest)
        if index < len(pending_urls):
            time.sleep(delay)

    click.echo(f"\nDone: {successes} succeeded, {failures} failed.")
    if failures:
        raise click.ClickException(f"{failures} candidate(s) failed to back up. See the manifest for details.")


@cli.command()
@_archive_root_option()
def verify(archive_root: Path | None) -> None:
    """Offline verification: recompute checksums of already-downloaded files."""
    resolved_root = _resolve_archive_root(archive_root)
    manifest = manifest_mod.load_manifest(resolved_root)

    successful_entries = [entry for entry in manifest.entries.values() if entry.status == manifest_mod.STATUS_SUCCESS]
    if not successful_entries:
        click.echo("No successfully archived media to verify yet.")
        return

    missing = 0
    mismatched = 0
    verified = 0
    manifest_changed = False
    for entry in successful_entries:
        if not entry.output_filename:
            continue
        file_path = resolved_root / entry.output_filename
        if not file_path.exists():
            click.echo(f"MISSING  {entry.output_filename} ({entry.source_url})")
            missing += 1
            continue
        actual_sha256 = manifest_mod.sha256_file(file_path)
        actual_size = file_path.stat().st_size
        if actual_sha256 != entry.sha256 or actual_size != entry.size_bytes:
            click.echo(f"MISMATCH {entry.output_filename} ({entry.source_url})")
            mismatched += 1
            continue
        verified += 1
        entry.last_verified_at = manifest_mod.current_timestamp()
        manifest_changed = True

    click.echo(f"\nVerified {verified} file(s); {missing} missing; {mismatched} mismatched.")
    if manifest_changed:
        manifest_mod.write_manifest(resolved_root, manifest)
    if missing or mismatched:
        raise click.ClickException(f"{missing + mismatched} file(s) failed verification.")


@cli.command("r2-sync")
@_archive_root_option()
@_r2_bucket_option()
def r2_sync(archive_root: Path | None, bucket: str) -> None:
    """Replicate verified media, manifests, checksums, and extractor metadata to private R2."""
    resolved_root = _resolve_archive_root(archive_root)
    try:
        result = r2.sync_archive(r2.create_client_from_environment(), resolved_root, bucket)
    except r2.R2ReplicaError as error:
        raise click.ClickException(str(error)) from error
    click.echo(f"R2 sync complete: {result.uploaded} uploaded; {result.skipped} already verified.")


@cli.command("r2-verify")
@_archive_root_option()
@_r2_bucket_option()
def r2_verify(archive_root: Path | None, bucket: str) -> None:
    """Verify that private R2 has every local object with its expected checksum metadata."""
    resolved_root = _resolve_archive_root(archive_root)
    try:
        result = r2.verify_remote_archive(r2.create_client_from_environment(), resolved_root, bucket)
    except r2.R2ReplicaError as error:
        raise click.ClickException(str(error)) from error
    click.echo(f"R2 verified {result.verified} object(s); {result.missing} missing; {result.mismatched} mismatched.")
    if result.missing or result.mismatched:
        raise click.ClickException(f"{result.missing + result.mismatched} R2 object(s) failed verification.")


@cli.command("r2-recover")
@_archive_root_option()
@_r2_bucket_option()
@click.option(
    "--output-filename",
    required=True,
    help="Relative media filename recorded in the local archive manifest.",
)
@click.option(
    "--destination",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="External path where the recovered media file will be written.",
)
@click.option("--force/--no-force", default=False, help="Replace an existing destination file.")
def r2_recover(
    archive_root: Path | None,
    bucket: str,
    output_filename: str,
    destination: Path,
    force: bool,
) -> None:
    """Restore one media file from private R2 and validate its manifest checksum."""
    resolved_root = _resolve_archive_root(archive_root)
    resolved_destination = destination.expanduser().resolve()
    if resolved_destination == REPO_ROOT or REPO_ROOT in resolved_destination.parents:
        raise click.ClickException(f"Refusing to write recovered media under the repository at {REPO_ROOT}.")
    try:
        r2.recover_media(
            r2.create_client_from_environment(),
            resolved_root,
            bucket,
            output_filename,
            resolved_destination,
            force=force,
        )
    except r2.R2ReplicaError as error:
        raise click.ClickException(str(error)) from error
    click.echo(f"Recovered and verified {output_filename} to {resolved_destination}")


if __name__ == "__main__":
    cli()
