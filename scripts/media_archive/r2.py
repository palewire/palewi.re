"""Private, resumable R2 replication for an external media archive."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Protocol

from botocore.exceptions import ClientError

from scripts.media_archive.manifest import (
    MANIFEST_FILENAME,
    STATUS_SUCCESS,
    Manifest,
    ManifestEntry,
    load_manifest,
    sha256_file,
)

CHECKSUMS_FILENAME = "checksums.sha256"
DEFAULT_BUCKET = "palewire-media-archive"
_SHA256_METADATA_KEY = "sha256"


class R2ReplicaError(RuntimeError):
    """Raised when an archive cannot be safely replicated or recovered."""


class SupportsR2(Protocol):
    """The small S3 client surface used by the local replication commands."""

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, Any]: ...

    def upload_file(self, Filename: str, Bucket: str, Key: str, ExtraArgs: dict[str, Any]) -> None: ...

    def put_object(
        self,
        *,
        Bucket: str,
        Key: str,
        Body: bytes,
        ContentType: str,
        Metadata: dict[str, str],
    ) -> dict[str, Any]: ...

    def download_file(self, Bucket: str, Key: str, Filename: str) -> None: ...


@dataclass(frozen=True)
class ArchiveObject:
    """A local archive object and the checksum expected at its private R2 key."""

    key: str
    size_bytes: int
    sha256: str
    path: Path | None = None
    body: bytes | None = None

    @property
    def content_type(self) -> str:
        if self.key.endswith(".json"):
            return "application/json"
        if self.key.endswith(".sha256"):
            return "text/plain; charset=utf-8"
        return "application/octet-stream"


@dataclass(frozen=True)
class ReplicationResult:
    """Counts from one complete sync or remote verification pass."""

    uploaded: int = 0
    skipped: int = 0
    verified: int = 0
    missing: int = 0
    mismatched: int = 0


def create_client_from_environment(environ: Mapping[str, str] | None = None) -> SupportsR2:
    """Create an R2 S3 client using only explicitly named environment variables."""
    values = os.environ if environ is None else environ
    required = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
    missing = [name for name in required if not values.get(name)]
    if missing:
        names = ", ".join(missing)
        raise R2ReplicaError(
            f"Missing {names}. Create bucket-scoped R2 S3 credentials and set them in your shell or private config."
        )

    import boto3

    account_id = values["R2_ACCOUNT_ID"]
    endpoint_url = values.get("R2_ENDPOINT_URL") or f"https://{account_id}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        aws_access_key_id=values["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=values["R2_SECRET_ACCESS_KEY"],
        endpoint_url=endpoint_url,
        region_name="auto",
    )


def _relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise R2ReplicaError(f"Archive path must be relative and stay inside the archive root: {value}")
    return path


def _local_object(archive_root: Path, relative_path: Path) -> ArchiveObject:
    path = (archive_root / relative_path).resolve()
    if archive_root not in path.parents or not path.is_file():
        raise R2ReplicaError(f"Missing archived file: {relative_path.as_posix()}")
    return ArchiveObject(
        key=relative_path.as_posix(),
        size_bytes=path.stat().st_size,
        sha256=sha256_file(path),
        path=path,
    )


def _entry_paths(entry: ManifestEntry) -> list[Path]:
    paths: list[Path] = []
    if entry.output_filename:
        paths.append(_relative_path(entry.output_filename))
    if entry.info_json_path:
        paths.append(_relative_path(entry.info_json_path))
    return paths


def collect_archive_objects(archive_root: Path) -> tuple[Manifest, list[ArchiveObject]]:
    """Return media, metadata, manifest, and a derived checksum listing for upload."""
    manifest_file = archive_root / MANIFEST_FILENAME
    if not manifest_file.is_file():
        raise R2ReplicaError(f"Missing archive manifest: {manifest_file}")

    manifest = load_manifest(archive_root)
    objects_by_key: dict[str, ArchiveObject] = {}
    for entry in manifest.entries.values():
        if entry.status == STATUS_SUCCESS:
            if not entry.output_filename:
                continue
            media = _local_object(archive_root, _relative_path(entry.output_filename))
            if media.size_bytes != entry.size_bytes or media.sha256 != entry.sha256:
                raise R2ReplicaError(
                    f"Local media does not match its manifest checksum: {media.key}. Run media-archive-verify first."
                )
            objects_by_key[media.key] = media
            for relative_path in _entry_paths(entry)[1:]:
                metadata = _local_object(archive_root, relative_path)
                objects_by_key[metadata.key] = metadata

    manifest_object = _local_object(archive_root, Path(MANIFEST_FILENAME))
    objects_by_key[manifest_object.key] = manifest_object
    objects = [objects_by_key[key] for key in sorted(objects_by_key)]
    checksum_body = "".join(f"{item.sha256}  {item.key}\n" for item in objects).encode()
    objects.append(
        ArchiveObject(
            key=CHECKSUMS_FILENAME,
            size_bytes=len(checksum_body),
            sha256=sha256(checksum_body).hexdigest(),
            body=checksum_body,
        )
    )
    return manifest, objects


def _head_object(client: SupportsR2, bucket: str, key: str) -> dict[str, Any] | None:
    try:
        return client.head_object(Bucket=bucket, Key=key)
    except ClientError as error:
        code = str(error.response.get("Error", {}).get("Code", ""))
        if code in {"404", "NoSuchKey", "NotFound"}:
            return None
        raise


def _matches_remote(remote: dict[str, Any] | None, item: ArchiveObject) -> bool:
    if remote is None or remote.get("ContentLength") != item.size_bytes:
        return False
    metadata = remote.get("Metadata", {})
    return isinstance(metadata, dict) and metadata.get(_SHA256_METADATA_KEY) == item.sha256


def _upload_object(client: SupportsR2, bucket: str, item: ArchiveObject) -> None:
    extra_args = {
        "ContentType": item.content_type,
        "Metadata": {_SHA256_METADATA_KEY: item.sha256},
    }
    if item.path is not None:
        client.upload_file(str(item.path), bucket, item.key, ExtraArgs=extra_args)
        return
    assert item.body is not None
    client.put_object(Bucket=bucket, Key=item.key, Body=item.body, **extra_args)


def sync_archive(client: SupportsR2, archive_root: Path, bucket: str) -> ReplicationResult:
    """Upload only objects that R2 cannot prove are byte-identical."""
    _, objects = collect_archive_objects(archive_root)
    uploaded = 0
    skipped = 0
    for item in objects:
        if _matches_remote(_head_object(client, bucket, item.key), item):
            skipped += 1
            continue
        _upload_object(client, bucket, item)
        uploaded += 1
    return ReplicationResult(uploaded=uploaded, skipped=skipped)


def verify_remote_archive(client: SupportsR2, archive_root: Path, bucket: str) -> ReplicationResult:
    """Compare local archive checksums and sizes to R2 object metadata without downloads."""
    _, objects = collect_archive_objects(archive_root)
    verified = 0
    missing = 0
    mismatched = 0
    for item in objects:
        remote = _head_object(client, bucket, item.key)
        if remote is None:
            missing += 1
        elif _matches_remote(remote, item):
            verified += 1
        else:
            mismatched += 1
    return ReplicationResult(verified=verified, missing=missing, mismatched=mismatched)


def recover_media(
    client: SupportsR2,
    archive_root: Path,
    bucket: str,
    output_filename: str,
    destination: Path,
    *,
    force: bool = False,
) -> None:
    """Restore one selected successful media file and validate it before keeping it."""
    requested_path = _relative_path(output_filename)
    manifest = load_manifest(archive_root)
    entry = next(
        (
            candidate
            for candidate in manifest.entries.values()
            if candidate.status == STATUS_SUCCESS and candidate.output_filename == requested_path.as_posix()
        ),
        None,
    )
    if entry is None or not entry.sha256 or entry.size_bytes is None:
        raise R2ReplicaError(f"No successful manifest entry found for {requested_path.as_posix()}")
    if destination.exists() and not force:
        raise R2ReplicaError(f"Destination already exists: {destination}. Pass --force to replace it.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".download",
        delete=False,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)
    recovered = False
    try:
        client.download_file(bucket, requested_path.as_posix(), str(temporary_path))
        if temporary_path.stat().st_size != entry.size_bytes or sha256_file(temporary_path) != entry.sha256:
            raise R2ReplicaError(f"Recovered file failed checksum verification: {requested_path.as_posix()}")
        temporary_path.replace(destination)
        recovered = True
    finally:
        if not recovered:
            temporary_path.unlink(missing_ok=True)
