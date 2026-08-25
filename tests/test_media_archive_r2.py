"""Tests for private R2 media archive replication without live cloud access."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict

import pytest
from botocore.exceptions import ClientError

from scripts.media_archive import manifest as manifest_mod
from scripts.media_archive import r2


class StoredObject(TypedDict):
    """One object retained by the fake S3 client."""

    body: bytes
    metadata: dict[str, str]


class FakeR2:
    """Small in-memory S3 client that records exactly what replica code sends."""

    def __init__(self) -> None:
        self.objects: dict[str, StoredObject] = {}

    def head_object(self, *, Bucket: str, Key: str):
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")
        stored = self.objects[Key]
        return {
            "ContentLength": len(stored["body"]),
            "Metadata": stored["metadata"],
        }

    def upload_file(self, Filename: str, Bucket: str, Key: str, ExtraArgs: dict[str, Any]) -> None:
        metadata = ExtraArgs["Metadata"]
        assert isinstance(metadata, dict)
        assert all(isinstance(key, str) and isinstance(value, str) for key, value in metadata.items())
        self.objects[Key] = {
            "body": Path(Filename).read_bytes(),
            "metadata": ExtraArgs["Metadata"],
        }

    def put_object(
        self,
        *,
        Bucket: str,
        Key: str,
        Body: bytes,
        ContentType: str,
        Metadata: dict[str, str],
    ) -> dict[str, object]:
        self.objects[Key] = {
            "body": Body,
            "metadata": Metadata,
        }
        return {}

    def download_file(self, Bucket: str, Key: str, Filename: str) -> None:
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "404"}}, "GetObject")
        Path(Filename).write_bytes(self.objects[Key]["body"])


def make_archive(archive_root: Path) -> tuple[Path, manifest_mod.ManifestEntry]:
    media_path = archive_root / "direct" / "clip.bin"
    metadata_path = archive_root / "direct" / "clip.info.json"
    media_path.parent.mkdir(parents=True)
    media_path.write_bytes(b"preserved media")
    metadata_path.write_text('{"extractor": "Fake"}\n', encoding="utf-8")
    entry = manifest_mod.ManifestEntry(
        source_url="https://example.com/clip.mp4",
        kind="direct",
        occurrences=[],
        status=manifest_mod.STATUS_SUCCESS,
        output_filename="direct/clip.bin",
        size_bytes=media_path.stat().st_size,
        sha256=manifest_mod.sha256_file(media_path),
        info_json_path="direct/clip.info.json",
    )
    manifest_mod.write_manifest(archive_root, manifest_mod.Manifest(entries={entry.source_url: entry}))
    return media_path, entry


def test_collect_archive_objects_includes_media_metadata_manifest_and_checksums(tmp_path):
    archive_root = tmp_path / "archive"
    make_archive(archive_root)

    _, objects = r2.collect_archive_objects(archive_root)

    assert [item.key for item in objects] == [
        "direct/clip.bin",
        "direct/clip.info.json",
        "manifest.json",
        "checksums.sha256",
    ]
    checksums = objects[-1]
    assert checksums.body is not None
    assert b"direct/clip.bin" in checksums.body
    assert b"manifest.json" in checksums.body


def test_sync_is_idempotent_and_uses_checksum_metadata(tmp_path):
    archive_root = tmp_path / "archive"
    make_archive(archive_root)
    client = FakeR2()

    first = r2.sync_archive(client, archive_root, "bucket")
    second = r2.sync_archive(client, archive_root, "bucket")

    assert first.uploaded == 4
    assert first.skipped == 0
    assert second.uploaded == 0
    assert second.skipped == 4
    assert client.objects["direct/clip.bin"]["metadata"] == {
        "sha256": manifest_mod.sha256_file(archive_root / "direct" / "clip.bin")
    }


def test_verify_remote_reports_missing_and_mismatched_objects(tmp_path):
    archive_root = tmp_path / "archive"
    make_archive(archive_root)
    client = FakeR2()
    r2.sync_archive(client, archive_root, "bucket")
    del client.objects["manifest.json"]
    client.objects["direct/clip.bin"]["metadata"] = {"sha256": "incorrect"}

    result = r2.verify_remote_archive(client, archive_root, "bucket")

    assert result.verified == 2
    assert result.missing == 1
    assert result.mismatched == 1


def test_recover_media_restores_and_verifies_selected_file(tmp_path):
    archive_root = tmp_path / "archive"
    media_path, entry = make_archive(archive_root)
    client = FakeR2()
    r2.sync_archive(client, archive_root, "bucket")
    media_path.unlink()
    destination = tmp_path / "restored" / "clip.bin"

    r2.recover_media(client, archive_root, "bucket", entry.output_filename or "", destination)

    assert destination.read_bytes() == b"preserved media"


def test_recover_media_rejects_existing_destination_and_bad_checksum(tmp_path):
    archive_root = tmp_path / "archive"
    _, entry = make_archive(archive_root)
    client = FakeR2()
    r2.sync_archive(client, archive_root, "bucket")
    destination = tmp_path / "restored.bin"
    destination.write_bytes(b"keep this")

    with pytest.raises(r2.R2ReplicaError, match="Destination already exists"):
        r2.recover_media(client, archive_root, "bucket", entry.output_filename or "", destination)

    client.objects["direct/clip.bin"]["body"] = b"corrupt"
    with pytest.raises(r2.R2ReplicaError, match="failed checksum"):
        r2.recover_media(client, archive_root, "bucket", entry.output_filename or "", destination, force=True)
    assert destination.read_bytes() == b"keep this"
    assert not (tmp_path / "restored.bin.download").exists()


def test_collect_archive_objects_rejects_missing_or_unsafe_media_paths(tmp_path):
    archive_root = tmp_path / "archive"
    manifest_mod.write_manifest(
        archive_root,
        manifest_mod.Manifest(
            entries={
                "https://example.com/clip.mp4": manifest_mod.ManifestEntry(
                    source_url="https://example.com/clip.mp4",
                    kind="direct",
                    occurrences=[],
                    status=manifest_mod.STATUS_SUCCESS,
                    output_filename="../not-allowed.bin",
                )
            }
        ),
    )

    with pytest.raises(r2.R2ReplicaError, match="must be relative"):
        r2.collect_archive_objects(archive_root)


def test_collect_archive_objects_requires_manifest(tmp_path):
    with pytest.raises(r2.R2ReplicaError, match="Missing archive manifest"):
        r2.collect_archive_objects(tmp_path / "archive")


def test_collect_archive_objects_requires_media_to_match_its_manifest(tmp_path):
    archive_root = tmp_path / "archive"
    media_path, _ = make_archive(archive_root)
    media_path.write_bytes(b"changed after backup")

    with pytest.raises(r2.R2ReplicaError, match="does not match its manifest checksum"):
        r2.collect_archive_objects(archive_root)


def test_create_client_requires_explicit_r2_environment_variables():
    with pytest.raises(r2.R2ReplicaError, match="R2_ACCOUNT_ID"):
        r2.create_client_from_environment({})
