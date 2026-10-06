"""Validated, durable state for public-page Wayback maintenance."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit, urlunsplit

LIVE_STATUSES = {"unknown", "live", "missing", "redirect", "error"}
ARCHIVE_STATUSES = {"unknown", "missing", "pending", "archived", "blocked"}
CHECK_STATUSES = {"", "success", "error"}
RECORD_FIELDS = {
    "url",
    "live_status",
    "archive_status",
    "archive_url",
    "snapshot_at",
    "last_check_at",
    "last_check_status",
    "last_verified_at",
    "last_submit_at",
    "pending_archive_url",
    "attempts",
    "next_retry_at",
    "last_error",
    "live_checked_at",
    "live_error",
}
MANIFEST_FIELDS = {
    "pages",
    "discovery_queue",
    "discovery_seen",
    "discovery_errors",
    "discovery_complete",
    "discovery_started_at",
}


class ArchiveError(RuntimeError):
    """Raised when archive state or an archive service response is invalid."""


def utc_now() -> str:
    """Return the current time as an ISO 8601 UTC string.

    Returns:
        Current UTC time with a ``Z`` suffix.

    Examples:
        ``utc_now().endswith("Z")`` is True.
    """
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@dataclass
class PageRecord:
    """Archive state for one normalized public page."""

    url: str
    live_status: str = "unknown"
    archive_status: str = "unknown"
    archive_url: str = ""
    snapshot_at: str = ""
    last_check_at: str = ""
    last_check_status: str = ""
    last_verified_at: str = ""
    last_submit_at: str = ""
    pending_archive_url: str = ""
    attempts: int = 0
    next_retry_at: str = ""
    last_error: str = ""
    live_checked_at: str = ""
    live_error: str = ""


@dataclass
class Manifest:
    """Persistent archive and discovery state."""

    pages: dict[str, PageRecord] = field(default_factory=dict)
    discovery_queue: list[str] = field(default_factory=list)
    discovery_seen: list[str] = field(default_factory=list)
    discovery_errors: dict[str, str] = field(default_factory=dict)
    discovery_complete: bool = False
    discovery_started_at: str = ""

    def page(self, url: str) -> PageRecord:
        """Get or create the record for a normalized public page.

        Args:
            url: Normalized ``https://palewi.re/`` page URL.

        Returns:
            The record held by this manifest.

        Raises:
            ArchiveError: The URL is outside the supported public scope.

        Examples:
            ``Manifest().page("https://palewi.re/posts/")`` creates a record.
        """
        _validate_page_url(url, "page URL")
        if url not in self.pages:
            self.pages[url] = PageRecord(url=url)
        return self.pages[url]


class ManifestStore:
    """Read and atomically write validated archive manifests."""

    def __init__(self, path: Path):
        """Create a store for one JSON manifest.

        Args:
            path: Location of the JSON manifest.

        Returns:
            None.

        Examples:
            ``ManifestStore(Path(".site-archive/manifest.json"))``.
        """
        self.path = path

    def load(self) -> Manifest:
        """Load a manifest, returning an empty one only when it is absent.

        Returns:
            The validated saved manifest or an empty manifest.

        Raises:
            ArchiveError: JSON or manifest data is malformed.

        Examples:
            ``store.load().pages`` returns the saved page mapping.
        """
        if not self.path.exists() and not self.path.is_symlink():
            return Manifest()
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ArchiveError(f"{self.path}: invalid manifest JSON: {error}") from error
        return _manifest_from_value(value, str(self.path))

    def save(self, manifest: Manifest) -> None:
        """Validate and atomically persist a manifest.

        Args:
            manifest: State to validate and write.

        Returns:
            None.

        Raises:
            ArchiveError: The manifest state is invalid.

        Examples:
            ``store.save(Manifest())`` writes an empty valid manifest.
        """
        value = _manifest_to_value(manifest)
        _manifest_from_value(value, str(self.path))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        try:
            temporary_path.write_text(
                json.dumps(value, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            temporary_path.replace(self.path)
        except OSError as error:
            raise ArchiveError(f"{self.path}: unable to save manifest: {error}") from error


def _manifest_to_value(manifest: Manifest) -> dict[str, Any]:
    """Convert a manifest into its sole supported JSON object shape.

    Args:
        manifest: Manifest instance to serialize.

    Returns:
        JSON-compatible state.

    Examples:
        ``_manifest_to_value(Manifest())["pages"]`` is an empty mapping.
    """
    if not isinstance(manifest, Manifest):
        raise ArchiveError("manifest: expected a Manifest")
    return {
        "pages": {url: asdict(record) for url, record in manifest.pages.items()},
        "discovery_queue": manifest.discovery_queue,
        "discovery_seen": manifest.discovery_seen,
        "discovery_errors": manifest.discovery_errors,
        "discovery_complete": manifest.discovery_complete,
        "discovery_started_at": manifest.discovery_started_at,
    }


def _manifest_from_value(value: Any, location: str) -> Manifest:
    """Validate and construct a manifest from decoded JSON data.

    Args:
        value: Decoded JSON value.
        location: Human-readable source path for errors.

    Returns:
        Fully validated manifest state.

    Examples:
        ``_manifest_from_value(data, "manifest.json")`` loads saved state.
    """
    if not isinstance(value, dict):
        raise ArchiveError(f"{location}: manifest must be a JSON object")
    _require_exact_fields(value, MANIFEST_FIELDS, location)
    pages_value = value["pages"]
    if not isinstance(pages_value, dict):
        raise ArchiveError(f"{location}: pages must be an object")
    pages: dict[str, PageRecord] = {}
    for url, record_value in pages_value.items():
        _validate_page_url(url, f"{location}: page key")
        record = _record_from_value(record_value, f"{location}: page {url}")
        if record.url != url:
            raise ArchiveError(f"{location}: page key and record URL differ for {url}")
        pages[url] = record
    queue = _url_list(value["discovery_queue"], f"{location}: discovery_queue")
    seen = _url_list(value["discovery_seen"], f"{location}: discovery_seen")
    if len(set(queue)) != len(queue) or len(set(seen)) != len(seen):
        raise ArchiveError(f"{location}: discovery queues cannot contain duplicate URLs")
    if set(queue) & set(seen):
        raise ArchiveError(f"{location}: a discovery URL cannot be queued and seen")
    errors_value = value["discovery_errors"]
    if not isinstance(errors_value, dict):
        raise ArchiveError(f"{location}: discovery_errors must be an object")
    errors: dict[str, str] = {}
    for url, error in errors_value.items():
        _validate_page_url(url, f"{location}: discovery error URL")
        if not isinstance(error, str) or not error:
            raise ArchiveError(f"{location}: discovery errors must be non-empty strings")
        errors[url] = error
    if type(value["discovery_complete"]) is not bool:
        raise ArchiveError(f"{location}: discovery_complete must be a boolean")
    if value["discovery_complete"] and (queue or errors):
        raise ArchiveError(f"{location}: discovery cannot be complete with queued URLs or errors")
    _validate_timestamp(value["discovery_started_at"], f"{location}: discovery_started_at")
    return Manifest(
        pages=pages,
        discovery_queue=queue,
        discovery_seen=seen,
        discovery_errors=errors,
        discovery_complete=value["discovery_complete"],
        discovery_started_at=value["discovery_started_at"],
    )


def _record_from_value(value: Any, location: str) -> PageRecord:
    """Validate and construct a page record from decoded JSON data.

    Args:
        value: Decoded page object.
        location: Human-readable source location for errors.

    Returns:
        Fully validated page record.

    Examples:
        ``_record_from_value(data, "page")`` reads one saved page.
    """
    if not isinstance(value, dict):
        raise ArchiveError(f"{location}: record must be an object")
    _require_exact_fields(value, RECORD_FIELDS, location)
    for field_name in ("url", "archive_url", "pending_archive_url", "last_error", "live_error"):
        if not isinstance(value[field_name], str):
            raise ArchiveError(f"{location}: {field_name} must be a string")
    _validate_page_url(value["url"], f"{location}: url")
    if not isinstance(value["live_status"], str) or value["live_status"] not in LIVE_STATUSES:
        raise ArchiveError(f"{location}: invalid live_status")
    if not isinstance(value["archive_status"], str) or value["archive_status"] not in ARCHIVE_STATUSES:
        raise ArchiveError(f"{location}: invalid archive_status")
    if not isinstance(value["last_check_status"], str) or value["last_check_status"] not in CHECK_STATUSES:
        raise ArchiveError(f"{location}: invalid last_check_status")
    if type(value["attempts"]) is not int or value["attempts"] < 0:
        raise ArchiveError(f"{location}: attempts must be a non-negative integer")
    for field_name in (
        "last_check_at",
        "last_verified_at",
        "last_submit_at",
        "next_retry_at",
        "live_checked_at",
    ):
        _validate_timestamp(value[field_name], f"{location}: {field_name}")
    _validate_snapshot_url(value["archive_url"], f"{location}: archive_url", value["url"])
    _validate_snapshot_url(value["pending_archive_url"], f"{location}: pending_archive_url", value["url"])
    if not isinstance(value["snapshot_at"], str):
        raise ArchiveError(f"{location}: snapshot_at must be a string")
    if value["snapshot_at"]:
        _validate_wayback_timestamp(value["snapshot_at"], f"{location}: snapshot_at")
    if value["archive_status"] == "archived" and (
        not value["archive_url"] or not value["snapshot_at"] or not value["last_verified_at"]
    ):
        raise ArchiveError(f"{location}: archived records require archive_url, snapshot_at, and last_verified_at")
    if value["archive_status"] == "pending" and not value["last_submit_at"]:
        raise ArchiveError(f"{location}: pending records require last_submit_at")
    if value["archive_url"] and value["snapshot_at"]:
        snapshot_timestamp = urlsplit(value["archive_url"]).path.split("/")[2][:14]
        if snapshot_timestamp != value["snapshot_at"]:
            raise ArchiveError(f"{location}: snapshot_at does not match archive_url")
    return PageRecord(**value)


def _require_exact_fields(value: dict[str, Any], fields: set[str], location: str) -> None:
    """Reject missing or unrecognized persisted fields.

    Args:
        value: Object whose keys are validated.
        fields: Exact permitted field names.
        location: Human-readable source location for errors.

    Returns:
        None.

    Examples:
        ``_require_exact_fields({"url": "x"}, {"url"}, "record")`` succeeds.
    """
    if set(value) != fields:
        missing = sorted(fields - set(value))
        extra = sorted(set(value) - fields)
        details = [
            *([f"missing {', '.join(missing)}"] if missing else []),
            *([f"unknown {', '.join(extra)}"] if extra else []),
        ]
        raise ArchiveError(f"{location}: invalid fields ({'; '.join(details)})")


def _url_list(value: Any, location: str) -> list[str]:
    """Validate a list of normalized same-site discovery URLs.

    Args:
        value: Decoded candidate URL list.
        location: Human-readable source location for errors.

    Returns:
        Copied validated URL list.

    Examples:
        ``_url_list(["https://palewi.re/sitemap.xml"], "queue")``.
    """
    if not isinstance(value, list):
        raise ArchiveError(f"{location}: must be a list")
    for url in value:
        _validate_page_url(url, location)
    return list(value)


def _validate_page_url(url: Any, location: str) -> None:
    """Validate one normalized URL within the public palewi.re scope.

    Args:
        url: Candidate URL.
        location: Human-readable source location for errors.

    Returns:
        None.

    Examples:
        ``_validate_page_url("https://palewi.re/posts/", "page")``.
    """
    if not isinstance(url, str) or not url:
        raise ArchiveError(f"{location}: must be a non-empty URL string")
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as error:
        raise ArchiveError(f"{location}: invalid URL") from error
    path = parsed.path or "/"
    if (
        parsed.scheme != "https"
        or parsed.hostname != "palewi.re"
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or parsed.query
        or parsed.fragment
        or any(character.isspace() or ord(character) < 32 for character in url)
        or "\\" in unquote(path)
        or "//" in unquote(path)
        or any(part in {".", ".."} for part in unquote(path).split("/"))
        or urlunsplit(("https", "palewi.re", path, "", "")) != url
    ):
        raise ArchiveError(f"{location}: must be a normalized https://palewi.re/ URL")


def _validate_snapshot_url(url: str, location: str, page_url: str) -> None:
    """Validate a Wayback snapshot URL against its original page URL.

    Args:
        url: Optional HTTPS snapshot URL.
        location: Human-readable source location for errors.
        page_url: Normalized original public page URL.

    Returns:
        None.

    Examples:
        ``_validate_snapshot_url("", "record", "https://palewi.re/")``.
    """
    if not url:
        return
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as error:
        raise ArchiveError(f"{location}: invalid snapshot URL") from error
    match = re.fullmatch(r"/web/(\d{14})(?:[a-z_]+)?/(https?://.+)", parsed.path)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "web.archive.org"
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or parsed.query
        or parsed.fragment
        or match is None
    ):
        raise ArchiveError(f"{location}: must be an HTTPS web.archive.org snapshot URL")
    assert match is not None
    _validate_wayback_timestamp(match.group(1), f"{location}: snapshot URL")
    try:
        original = urlsplit(match.group(2))
        original_port = original.port
    except ValueError as error:
        raise ArchiveError(f"{location}: snapshot must match its page URL") from error
    page = urlsplit(page_url)
    if (
        original.scheme not in {"http", "https"}
        or original.hostname not in {"palewi.re", "www.palewi.re"}
        or original.username is not None
        or original.password is not None
        or original_port not in {None, 80 if original.scheme == "http" else 443}
        or original.query
        or original.fragment
        or (original.path != page.path and not paths_differ_only_by_trailing_slash(original.path, page.path))
    ):
        raise ArchiveError(f"{location}: snapshot must match its page URL")


def paths_differ_only_by_trailing_slash(first: str, second: str) -> bool:
    """Check whether two paths differ only by one final slash.

    Args:
        first: First URL path.
        second: Second URL path.

    Returns:
        Whether either path is the other path with exactly one trailing slash.

    Examples:
        ``paths_differ_only_by_trailing_slash("/docs/week-1", "/docs/week-1/")`` is True.
    """
    return (first.endswith("/") and not second.endswith("/") and first[:-1] == second) or (
        second.endswith("/") and not first.endswith("/") and second[:-1] == first
    )


def _validate_wayback_timestamp(value: str, location: str) -> None:
    """Validate a 14-digit timestamp as a real UTC calendar date.

    Args:
        value: Wayback timestamp in ``YYYYMMDDhhmmss`` form.
        location: Human-readable source location for errors.

    Returns:
        None.

    Examples:
        ``_validate_wayback_timestamp("20260905120000", "snapshot")``.
    """
    if len(value) != 14 or not value.isdigit():
        raise ArchiveError(f"{location}: snapshot_at must be a 14-digit Wayback timestamp")
    try:
        datetime.strptime(value, "%Y%m%d%H%M%S")
    except ValueError as error:
        raise ArchiveError(f"{location}: snapshot_at must be a real UTC timestamp") from error


def _validate_timestamp(value: Any, location: str) -> None:
    """Validate an optional ISO 8601 timestamp written in UTC.

    Args:
        value: Empty string or ISO UTC timestamp.
        location: Human-readable source location for errors.

    Returns:
        None.

    Examples:
        ``_validate_timestamp("2026-09-05T12:00:00Z", "checked")``.
    """
    if not isinstance(value, str):
        raise ArchiveError(f"{location}: must be an ISO UTC timestamp string")
    if not value:
        return
    if not value.endswith(("Z", "+00:00")):
        raise ArchiveError(f"{location}: must be a UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ArchiveError(f"{location}: invalid ISO UTC timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ArchiveError(f"{location}: must be a UTC timestamp")
