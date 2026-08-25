"""Tests for the atomic media archive manifest."""

import hashlib
import json

import pytest

from scripts.media_archive.discovery import MediaCandidate, MediaOccurrence
from scripts.media_archive.manifest import (
    STATUS_PENDING,
    STATUS_SUCCESS,
    Manifest,
    ManifestEntry,
    ManifestError,
    load_manifest,
    manifest_path,
    occurrence_to_dict,
    sha256_file,
    sync_candidates,
    write_manifest,
)


def make_candidate(url: str, kind: str = "direct") -> MediaCandidate:
    return MediaCandidate(
        url=url,
        kind=kind,
        occurrences=(MediaOccurrence("post", "example-post", "video", url),),
    )


def test_manifest_entry_round_trips_through_dict():
    entry = ManifestEntry(source_url="https://example.com/a.mp4", kind="direct", occurrences=[])
    entry.status = STATUS_SUCCESS
    entry.size_bytes = 123
    restored = ManifestEntry.from_dict(entry.to_dict())
    assert restored == entry


def test_manifest_entry_from_dict_ignores_unknown_fields():
    restored = ManifestEntry.from_dict(
        {"source_url": "https://example.com/a.mp4", "kind": "direct", "occurrences": [], "future_field": "x"}
    )
    assert restored.source_url == "https://example.com/a.mp4"


def test_manifest_round_trips_and_sorts_entries():
    manifest = Manifest()
    manifest.entries["https://b.example.com"] = ManifestEntry(
        source_url="https://b.example.com", kind="direct", occurrences=[]
    )
    manifest.entries["https://a.example.com"] = ManifestEntry(
        source_url="https://a.example.com", kind="direct", occurrences=[]
    )

    data = manifest.to_dict()

    assert list(data["entries"].keys()) == ["https://a.example.com", "https://b.example.com"]
    restored = Manifest.from_dict(data)
    assert set(restored.entries) == {"https://a.example.com", "https://b.example.com"}


def test_manifest_from_dict_defaults_missing_entries():
    restored = Manifest.from_dict({})
    assert restored.entries == {}
    assert restored.version == 1


def test_load_manifest_missing_file_returns_empty(tmp_path):
    manifest = load_manifest(tmp_path)
    assert manifest.entries == {}


def test_load_manifest_invalid_json_raises(tmp_path):
    manifest_path(tmp_path).write_text("not json", encoding="utf-8")
    try:
        load_manifest(tmp_path)
        raise AssertionError("expected ManifestError")
    except ManifestError as error:
        assert "not valid JSON" in str(error)


def test_load_manifest_non_object_raises(tmp_path):
    manifest_path(tmp_path).write_text("[1, 2, 3]", encoding="utf-8")
    try:
        load_manifest(tmp_path)
        raise AssertionError("expected ManifestError")
    except ManifestError as error:
        assert "must be a JSON object" in str(error)


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ('{"entries": null}', "manifest 'entries' must be a JSON object"),
        ('{"entries": {"https://example.com/a.mp4": []}}', "manifest entry for 'https://example.com/a.mp4'"),
    ],
)
def test_load_manifest_invalid_entry_shapes_raise_manifest_error(tmp_path, contents, message):
    manifest_path(tmp_path).write_text(contents, encoding="utf-8")

    with pytest.raises(ManifestError, match=message):
        load_manifest(tmp_path)


def test_write_manifest_is_atomic_and_readable(tmp_path):
    manifest = Manifest()
    manifest.entries["https://example.com/a.mp4"] = ManifestEntry(
        source_url="https://example.com/a.mp4", kind="direct", occurrences=[]
    )

    write_manifest(tmp_path, manifest)

    assert manifest_path(tmp_path).exists()
    assert not (tmp_path / "manifest.json.tmp").exists()
    reloaded = load_manifest(tmp_path)
    assert "https://example.com/a.mp4" in reloaded.entries
    data = json.loads(manifest_path(tmp_path).read_text(encoding="utf-8"))
    assert data["version"] == 1


def test_write_manifest_creates_archive_root(tmp_path):
    archive_root = tmp_path / "nested" / "archive"
    write_manifest(archive_root, Manifest())
    assert archive_root.is_dir()
    assert manifest_path(archive_root).exists()


def test_sha256_file_matches_known_digest(tmp_path):
    path = tmp_path / "file.bin"
    path.write_bytes(b"hello world")
    assert sha256_file(path) == hashlib.sha256(b"hello world").hexdigest()


def test_sha256_file_reads_in_chunks_for_large_file(tmp_path):
    payload = b"x" * (2 * 1024 * 1024 + 17)
    path = tmp_path / "big.bin"
    path.write_bytes(payload)
    assert sha256_file(path) == hashlib.sha256(payload).hexdigest()


def test_occurrence_to_dict():
    occurrence = MediaOccurrence("post", "slug", "video", "https://example.com/a.mp4")
    assert occurrence_to_dict(occurrence) == {
        "origin_type": "post",
        "origin_id": "slug",
        "location": "video",
        "raw_url": "https://example.com/a.mp4",
    }


def test_sync_candidates_adds_new_pending_entries():
    manifest = Manifest()
    candidate = make_candidate("https://example.com/a.mp4")

    sync_candidates(manifest, [candidate])

    entry = manifest.entries["https://example.com/a.mp4"]
    assert entry.status == STATUS_PENDING
    assert entry.kind == "direct"
    assert entry.occurrences == [occurrence_to_dict(candidate.occurrences[0])]


def test_sync_candidates_preserves_existing_status_and_history():
    manifest = Manifest()
    candidate = make_candidate("https://example.com/a.mp4")
    sync_candidates(manifest, [candidate])
    manifest.entries["https://example.com/a.mp4"].status = STATUS_SUCCESS
    manifest.entries["https://example.com/a.mp4"].sha256 = "deadbeef"

    updated_candidate = MediaCandidate(
        url="https://example.com/a.mp4",
        kind="direct",
        occurrences=(MediaOccurrence("post", "second-post", "video", "https://example.com/a.mp4"),),
    )
    sync_candidates(manifest, [updated_candidate])

    entry = manifest.entries["https://example.com/a.mp4"]
    assert entry.status == STATUS_SUCCESS
    assert entry.sha256 == "deadbeef"
    assert entry.occurrences == [occurrence_to_dict(updated_candidate.occurrences[0])]


def test_sync_candidates_does_not_remove_stale_entries():
    manifest = Manifest()
    manifest.entries["https://stale.example.com/a.mp4"] = ManifestEntry(
        source_url="https://stale.example.com/a.mp4", kind="direct", occurrences=[]
    )

    sync_candidates(manifest, [make_candidate("https://example.com/a.mp4")])

    assert "https://stale.example.com/a.mp4" in manifest.entries
    assert "https://example.com/a.mp4" in manifest.entries
