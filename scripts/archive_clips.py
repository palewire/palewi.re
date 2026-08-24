"""Archive clip URLs with the Internet Archive's Wayback Machine."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import click
import requests
import yaml
from savepagenow import BlockedByRobots, capture
from savepagenow.exceptions import BadGateway, TooManyRequests, UnknownError, WaybackRuntimeError

from coltrane.content_loaders import ContentError, load_clips

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "coltrane" / "content" / "clips.yaml"
AVAILABILITY_URL = "https://archive.org/wayback/available"
USER_AGENT = "palewi.re clip archiver (https://github.com/palewire/palewi.re)"
TRANSIENT_CAPTURE_ERRORS = (BadGateway, TooManyRequests, UnknownError, requests.RequestException)


class ArchiveError(RuntimeError):
    """Raised when clip archive data or a Wayback response is invalid."""


def load_document(path: Path) -> dict[str, Any]:
    """Load the clips YAML document."""
    try:
        load_clips(path)
    except ContentError as error:
        raise ArchiveError(str(error)) from error
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or not isinstance(document.get("clips"), list):
        raise ArchiveError(f"{path}: expected a top-level 'clips' list")
    for record in document["clips"]:
        if not isinstance(record, dict) or not isinstance(record.get("url"), str):
            raise ArchiveError(f"{path}: every clip must be a mapping with a URL")
    return document


def write_document(path: Path, document: dict[str, Any]) -> None:
    """Atomically write archive metadata without reordering clip fields."""
    content = yaml.safe_dump(document, allow_unicode=True, default_flow_style=False, sort_keys=False)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    temporary_path.write_text(content, encoding="utf-8")
    temporary_path.replace(path)


def normalize_snapshot_url(url: str) -> str:
    """Return a secure Wayback snapshot URL."""
    if url.startswith("http://web.archive.org/"):
        return f"https://{url.removeprefix('http://')}"
    return url


def lookup_existing_snapshot(url: str, timeout: float = 30) -> str | None:
    """Return the closest available Wayback snapshot for a URL."""
    response = requests.get(
        AVAILABILITY_URL,
        params={"url": url},
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ArchiveError(f"Wayback returned an invalid availability response for {url}")
    snapshots = payload.get("archived_snapshots")
    if not isinstance(snapshots, dict):
        return None
    closest = snapshots.get("closest")
    if not isinstance(closest, dict):
        return None
    if closest.get("available") is not True or closest.get("status") != "200":
        return None
    snapshot_url = closest.get("url")
    if not isinstance(snapshot_url, str) or not snapshot_url:
        raise ArchiveError(f"Wayback returned an invalid snapshot URL for {url}")
    return normalize_snapshot_url(snapshot_url)


def require_credentials() -> None:
    """Require Internet Archive credentials before requesting a capture."""
    missing = [name for name in ("SAVEPAGENOW_ACCESS_KEY", "SAVEPAGENOW_SECRET_KEY") if not os.environ.get(name)]
    if missing:
        names = " and ".join(missing)
        raise ArchiveError(f"{names} must be set to create new Wayback captures")


def capture_with_retries(
    url: str,
    *,
    attempts: int = 3,
    retry_delay: float = 10,
    capture_page: Callable[..., str] = capture,
) -> str:
    """Capture a URL, retrying only errors that are likely temporary."""
    require_credentials()
    for attempt in range(1, attempts + 1):
        try:
            snapshot_url = capture_page(
                url,
                user_agent=USER_AGENT,
                accept_cache=True,
                authenticate=True,
            )
            if not isinstance(snapshot_url, str) or not snapshot_url:
                raise ArchiveError(f"Wayback returned an invalid snapshot URL for {url}")
            return normalize_snapshot_url(snapshot_url)
        except TRANSIENT_CAPTURE_ERRORS:
            if attempt == attempts:
                raise
            time.sleep(retry_delay * attempt)
    raise ArchiveError(f"Wayback did not return a snapshot for {url}")


def pending_records(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Return clips without a snapshot or an explicit exemption."""
    return [
        record for record in document["clips"] if not record.get("archive_url") and not record.get("archive_exemption")
    ]


def archive_record(record: dict[str, Any], *, retry_delay: float, skip_missing: bool = False) -> str:
    """Archive one clip and return a short outcome label."""
    url = record["url"]
    if url.startswith(("https://web.archive.org/", "http://web.archive.org/")):
        record["archive_url"] = normalize_snapshot_url(url)
        return "already a Wayback URL"

    existing_snapshot = lookup_existing_snapshot(url)
    if existing_snapshot:
        record["archive_url"] = normalize_snapshot_url(existing_snapshot)
        return "found existing snapshot"

    if skip_missing:
        return "skipped (no existing snapshot)"

    try:
        record["archive_url"] = capture_with_retries(url, retry_delay=retry_delay)
    except BlockedByRobots:
        record["archive_exemption"] = "Wayback capture blocked by the publisher's robots policy"
        return "recorded robots-policy exemption"
    return "created snapshot"


@click.group()
def cli() -> None:
    """Archive and validate URLs in coltrane/content/clips.yaml."""


@cli.command()
@click.option("--path", type=click.Path(path_type=Path), default=DEFAULT_PATH, show_default=True)
@click.option("--limit", type=click.IntRange(min=1), help="Process at most this many pending clips.")
@click.option("--delay", type=click.FloatRange(min=0), default=2.0, show_default=True)
@click.option("--retry-delay", type=click.FloatRange(min=0), default=10.0, show_default=True)
@click.option(
    "--skip-missing",
    is_flag=True,
    help="Skip clips without existing Wayback snapshots instead of creating new captures.",
)
def archive(path: Path, limit: int | None, delay: float, retry_delay: float, skip_missing: bool) -> None:
    """Archive clips missing Wayback metadata, saving after every result."""
    try:
        document = load_document(path)
        records = pending_records(document)
        if limit is not None:
            records = records[:limit]
        if not records:
            click.echo("All clip URLs have archive metadata.")
            return

        skipped_count = 0
        for index, record in enumerate(records, start=1):
            title = record.get("title", record["url"])
            click.echo(f"[{index}/{len(records)}] {title}")
            outcome = archive_record(record, retry_delay=retry_delay, skip_missing=skip_missing)
            write_document(path, document)
            click.echo(f"  {outcome}")
            if outcome == "skipped (no existing snapshot)":
                skipped_count += 1
            if index < len(records):
                time.sleep(delay)

        if skip_missing and skipped_count > 0:
            click.echo(
                f"\nSkipped {skipped_count} clips without existing snapshots "
                "(requires credentials to create new captures)."
            )
    except (ArchiveError, WaybackRuntimeError, requests.RequestException) as error:
        raise click.ClickException(str(error)) from error


@cli.command(name="check")
@click.option("--path", type=click.Path(path_type=Path), default=DEFAULT_PATH, show_default=True)
def check_archives(path: Path) -> None:
    """Fail if any clip lacks a snapshot URL or an explicit exemption."""
    try:
        document = load_document(path)
    except ArchiveError as error:
        raise click.ClickException(str(error)) from error
    records = pending_records(document)
    if records:
        preview = "\n".join(f"  - {record.get('title', record['url'])}: {record['url']}" for record in records[:10])
        remainder = len(records) - 10
        suffix = f"\n  ... and {remainder} more" if remainder > 0 else ""
        raise click.ClickException(f"{len(records)} clip URL(s) lack archive metadata:\n{preview}{suffix}")
    click.echo(f"All {len(document['clips'])} clip URLs have archive metadata.")


if __name__ == "__main__":
    cli()
