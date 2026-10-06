"""Tests for strict site archive manifest persistence."""

import json
from pathlib import Path
from typing import cast

import pytest

from scripts.site_archive.manifest import ArchiveError, Manifest, ManifestStore, PageRecord, utc_now

URL = "https://palewi.re/posts/"
SNAPSHOT = "https://web.archive.org/web/20260905120000/https://palewi.re/posts/"


def test_manifest_rejects_contradictory_coverage(tmp_path: Path) -> None:
    """Reject completion claims that disagree with the saved evidence.

    Args:
        tmp_path: Temporary test directory.

    Returns:
        None.

    Examples:
        A nonempty discovery queue cannot be reported as complete.
    """
    store = ManifestStore(tmp_path / "manifest.json")
    state = Manifest(discovery_complete=True, discovery_queue=[URL])
    with pytest.raises(ArchiveError, match="cannot be complete"):
        store.save(state)
    state = Manifest()
    page = state.page(URL)
    page.archive_url = SNAPSHOT
    page.snapshot_at = "20260904120000"
    with pytest.raises(ArchiveError, match="does not match"):
        store.save(state)


def test_manifest_rejects_invalid_encoding_and_broken_links(tmp_path: Path) -> None:
    """Do not treat unreadable state as an absent manifest.

    Args:
        tmp_path: Temporary test directory.

    Returns:
        None.

    Examples:
        A broken manifest symlink raises an error instead of starting over.
    """
    path = tmp_path / "manifest.json"
    path.write_bytes(b"\xff")
    with pytest.raises(ArchiveError, match="invalid manifest"):
        ManifestStore(path).load()
    link = tmp_path / "broken.json"
    link.symlink_to(tmp_path / "absent.json")
    with pytest.raises(ArchiveError, match="invalid manifest"):
        ManifestStore(link).load()


def test_manifest_round_trip_creates_pages_and_writes_atomically(tmp_path: Path) -> None:
    """Persist all supported fields and reload their typed defaults.

    Args:
        tmp_path: Temporary test directory.

    Returns:
        None.

    Examples:
        New state records a page through ``Manifest.page``.
    """
    path = tmp_path / "state" / "manifest.json"
    manifest = Manifest()
    page = manifest.page(URL)
    page.live_status = "live"
    page.archive_status = "archived"
    page.archive_url = SNAPSHOT
    page.snapshot_at = "20260905120000"
    page.last_verified_at = utc_now()
    manifest.discovery_complete = True
    ManifestStore(path).save(manifest)

    saved = json.loads(path.read_text())
    assert set(saved) == {
        "pages",
        "discovery_queue",
        "discovery_seen",
        "discovery_errors",
        "discovery_complete",
        "discovery_started_at",
    }
    assert not path.with_suffix(".json.tmp").exists()
    loaded = ManifestStore(path).load()
    assert loaded.pages[URL] == page
    assert loaded.discovery_complete is True


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ("not json", "invalid manifest JSON"),
        ('{"pages": {}}', "invalid fields"),
        (
            '{"pages":{"http://palewi.re/posts/":{"url":"http://palewi.re/posts/"}},"discovery_queue":[],'
            '"discovery_seen":[],"discovery_errors":{},"discovery_complete":false,"discovery_started_at":""}',
            "normalized",
        ),
    ],
)
def test_manifest_rejects_corrupt_or_incomplete_inputs(tmp_path: Path, contents: str, message: str) -> None:
    """Reject corrupt data instead of silently resetting saved state.

    Args:
        tmp_path: Temporary test directory.
        contents: Invalid JSON document.
        message: Expected error fragment.

    Returns:
        None.

    Examples:
        A file with invalid JSON raises ``ArchiveError``.
    """
    path = tmp_path / "manifest.json"
    path.write_text(contents)
    with pytest.raises(ArchiveError, match=message):
        ManifestStore(path).load()
    assert path.read_text() == contents


@pytest.mark.parametrize(
    "url",
    [
        "https://www.palewi.re/posts/",
        "https://palewi.re/posts/?page=2",
        "https://palewi.re/posts/#top",
        "https://palewi.re/a//b/",
        "https://palewi.re/a/../b/",
    ],
)
def test_manifest_rejects_non_normalized_page_urls(url: str) -> None:
    """Reject URLs that could expand archive scope or duplicate coverage.

    Args:
        url: Invalid page URL.

    Returns:
        None.

    Examples:
        Query-bearing URLs cannot become manifest keys.
    """
    with pytest.raises(ArchiveError, match="normalized"):
        Manifest().page(url)


def test_manifest_rejects_invalid_record_types_and_snapshot_urls(tmp_path: Path) -> None:
    """Validate types, UTC timestamps, statuses, and matching snapshots.

    Args:
        tmp_path: Temporary test directory.

    Returns:
        None.

    Examples:
        A page snapshot for another URL is rejected.
    """
    path = tmp_path / "manifest.json"
    state = Manifest()
    page = state.page(URL)
    page.live_status = "not-live"
    with pytest.raises(ArchiveError, match="live_status"):
        ManifestStore(path).save(state)

    page.live_status = "live"
    page.last_check_at = "2026-09-05T12:00:00+02:00"
    with pytest.raises(ArchiveError, match="UTC timestamp"):
        ManifestStore(path).save(state)

    page.last_check_at = ""
    page.archive_url = "https://web.archive.org/web/20260905120000/https://palewi.re/elsewhere/"
    with pytest.raises(ArchiveError, match="match its page"):
        ManifestStore(path).save(state)

    page.archive_url = SNAPSHOT
    page.attempts = True
    with pytest.raises(ArchiveError, match="non-negative integer"):
        ManifestStore(path).save(state)


def test_manifest_requires_confirmed_and_pending_archive_evidence(tmp_path: Path) -> None:
    """Reject archive statuses that would incorrectly claim durable coverage.

    Args:
        tmp_path: Temporary test directory.

    Returns:
        None.

    Examples:
        An archived record cannot omit when its snapshot was verified.
    """
    path = tmp_path / "manifest.json"
    archived = Manifest()
    page = archived.page(URL)
    page.archive_status = "archived"
    page.archive_url = SNAPSHOT
    page.snapshot_at = "20260905120000"
    with pytest.raises(ArchiveError, match="last_verified_at"):
        ManifestStore(path).save(archived)

    page.last_verified_at = utc_now()
    ManifestStore(path).save(archived)
    corrupted = json.loads(path.read_text())
    corrupted["pages"][URL]["snapshot_at"] = 0
    path.write_text(json.dumps(corrupted))
    with pytest.raises(ArchiveError, match="snapshot_at must be a string"):
        ManifestStore(path).load()

    pending = Manifest()
    pending.page(URL).archive_status = "pending"
    with pytest.raises(ArchiveError, match="last_submit_at"):
        ManifestStore(path).save(pending)


def test_manifest_round_trips_a_one_trailing_slash_snapshot_alias(tmp_path: Path) -> None:
    """Allow runtime-proven snapshot aliases to remain in saved state.

    Args:
        tmp_path: Temporary test directory.

    Returns:
        None.

    Examples:
        An archived ``/posts`` snapshot may belong to canonical ``/posts/``.
    """
    path = tmp_path / "manifest.json"
    state = Manifest()
    page = state.page(URL)
    page.live_status = "live"
    page.archive_status = "archived"
    page.archive_url = SNAPSHOT.rstrip("/")
    page.snapshot_at = "20260905120000"
    page.last_verified_at = utc_now()
    ManifestStore(path).save(state)
    assert ManifestStore(path).load().pages[URL].archive_url == SNAPSHOT.rstrip("/")


def test_manifest_rejects_impossible_snapshot_dates(tmp_path: Path) -> None:
    """Reject digit-only timestamps that are not real dates.

    Args:
        tmp_path: Temporary test directory.

    Returns:
        None.

    Examples:
        February 30 cannot identify an archived page.
    """
    path = tmp_path / "manifest.json"
    state = Manifest()
    page = state.page(URL)
    page.archive_status = "archived"
    page.archive_url = "https://web.archive.org/web/20260230000000/https://palewi.re/posts/"
    page.snapshot_at = "20260230000000"
    page.last_verified_at = utc_now()
    with pytest.raises(ArchiveError, match="real UTC timestamp"):
        ManifestStore(path).save(state)


def test_absent_manifest_returns_empty_but_invalid_object_does_not(tmp_path: Path) -> None:
    """Distinguish a first run from malformed persisted state.

    Args:
        tmp_path: Temporary test directory.

    Returns:
        None.

    Examples:
        A missing file returns an empty ``Manifest``.
    """
    path = tmp_path / "manifest.json"
    assert ManifestStore(path).load() == Manifest()
    with pytest.raises(ArchiveError, match="expected a Manifest"):
        ManifestStore(path).save(cast(Manifest, PageRecord(url=URL)))


def test_manifest_allows_normalized_sitemaps_in_discovery_state(tmp_path: Path) -> None:
    """Persist sitemap work without treating it as an archiveable HTML page.

    Args:
        tmp_path: Temporary test directory.

    Returns:
        None.

    Examples:
        Sitemap URLs can occur in queues, seen lists, and discovery errors.
    """
    path = tmp_path / "manifest.json"
    sitemap = "https://palewi.re/sitemap.xml"
    manifest = Manifest(
        discovery_queue=[sitemap],
        discovery_seen=[URL],
        discovery_errors={sitemap: "HTTP 503"},
    )
    ManifestStore(path).save(manifest)
    assert ManifestStore(path).load() == manifest
