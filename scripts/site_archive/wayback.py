"""Wayback availability checks and deliberate page-capture requests."""

from __future__ import annotations

import os
import re
import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any, Protocol
from urllib.parse import urlsplit

import requests
from savepagenow import BlockedByRobots
from savepagenow import capture as save_capture
from savepagenow.exceptions import BadGateway, TooManyRequests, UnknownError, WaybackRuntimeError

from scripts.site_archive.manifest import ArchiveError, PageRecord

AVAILABILITY_URL = "https://archive.org/wayback/available"
USER_AGENT = "palewi.re site archiver (https://github.com/palewire/palewi.re)"
PENDING_COOLDOWN = timedelta(hours=24)
MAX_RETRY_DELAY = timedelta(hours=24)
SNAPSHOT_PATH = re.compile(r"^/web/(\d{14})(?:[a-z_]+)?/(https?://.+)$")


class HttpSession(Protocol):
    """Subset of a requests session used by availability lookups."""

    def get(self, url: str, **kwargs: object) -> requests.Response:
        """Send one HTTP GET request.

        Args:
            url: Request URL.
            **kwargs: Requests-compatible request options.

        Returns:
            HTTP response.

        Examples:
            ``session.get("https://archive.org/wayback/available")``.
        """


class WaybackClient:
    """Maintain archive state using Wayback's availability and save APIs."""

    def __init__(
        self,
        *,
        timeout: float = 30.0,
        capture_delay: float = 12.0,
        lookup_delay: float = 1.0,
        session: HttpSession | None = None,
        capture_page: Callable[..., str] = save_capture,
        clock: Callable[[], datetime] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
        checkpoint: Callable[[], None] | None = None,
    ):
        """Configure a rate-limited Wayback client.

        Args:
            timeout: Per-request timeout in seconds.
            capture_delay: Minimum delay between capture submissions.
            lookup_delay: Minimum delay between availability lookups.
            session: Optional requests session for testing or customization.
            capture_page: Save Page Now callable.
            clock: UTC clock used for recorded timestamps.
            sleep: Delay function used for rate limiting.
            monotonic: Monotonic clock used for rate limiting.
            checkpoint: Persist pending state before a capture request leaves the process.

        Returns:
            None.

        Examples:
            ``WaybackClient(timeout=10.0).verify(page)`` checks one page.
        """
        self.timeout = timeout
        self.capture_delay = capture_delay
        self.lookup_delay = lookup_delay
        self.session = session or requests.Session()
        self.capture_page = capture_page
        self.clock = clock or (lambda: datetime.now(UTC))
        self.sleep = sleep
        self.monotonic = monotonic
        self.checkpoint = checkpoint
        self._last_lookup: float | None = None
        self._last_capture: float | None = None

    def verify(self, page: PageRecord) -> None:
        """Check whether Wayback has a verified snapshot for a page.

        Args:
            page: Mutable page record to check.

        Returns:
            None. Updates confirmed coverage or a resumable error state.

        Raises:
            ArchiveError: Wayback returns malformed data or cannot be reached.

        Examples:
            ``client.verify(PageRecord(url="https://palewi.re/posts/"))``.
        """
        self._wait_for("lookup")
        now = self._now()
        try:
            response = self.session.get(
                AVAILABILITY_URL,
                params={"url": page.url},
                headers={"User-Agent": USER_AGENT},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            snapshot = _availability_snapshot(payload, page.url)
        except (requests.RequestException, ValueError, ArchiveError) as error:
            message = _safe_error(error, operation="availability check")
            self._record_error(page, message, _retry_after(error, self._datetime()))
            raise ArchiveError(f"{page.url}: {message}") from error

        page.last_check_at = now
        page.last_check_status = "success"
        page.last_error = ""
        page.next_retry_at = ""
        page.attempts = 0
        if snapshot is None:
            if page.archive_status == "pending" and _pending_is_fresh(page, self._datetime()):
                return
            page.archive_status = "missing"
            page.archive_url = ""
            page.snapshot_at = ""
            page.pending_archive_url = ""
            return
        snapshot_url, timestamp = snapshot
        page.archive_status = "archived"
        page.archive_url = snapshot_url
        page.snapshot_at = timestamp
        page.last_verified_at = now
        page.pending_archive_url = ""

    def capture(self, page: PageRecord) -> None:
        """Submit a missing live page after checking Wayback one more time.

        Args:
            page: Mutable live record currently believed to be missing.

        Returns:
            None. A successful submission is recorded as pending confirmation.

        Raises:
            ArchiveError: Credentials, service data, or capture submission fail.

        Examples:
            ``client.capture(PageRecord(url="https://palewi.re/posts/", live_status="live", archive_status="missing"))``.
        """
        try:
            _require_credentials()
        except ArchiveError as error:
            self._record_error(page, _safe_error(error, operation="capture"), None)
            raise
        if page.live_status != "live" or page.archive_status not in {"missing", "pending"}:
            raise ArchiveError(f"{page.url}: only live pages missing an archive can be captured")
        if page.archive_status == "pending" and _pending_is_fresh(page, self._datetime()):
            return
        self.verify(page)
        if page.archive_status != "missing" or page.live_status != "live":
            return

        page.archive_status = "pending"
        page.pending_archive_url = ""
        page.last_submit_at = self._now()
        page.last_error = ""
        page.next_retry_at = ""
        page.attempts = 0
        self._wait_for("capture")
        if self.checkpoint is not None:
            self.checkpoint()
        try:
            snapshot_url = self.capture_page(
                page.url,
                user_agent=USER_AGENT,
                accept_cache=True,
                timeout=max(1, int(self.timeout)),
                authenticate=True,
            )
            if not isinstance(snapshot_url, str):
                raise ArchiveError("Wayback capture returned no snapshot URL")
            normalized, _ = _validate_snapshot(snapshot_url, page.url)
        except BlockedByRobots:
            page.archive_status = "blocked"
            page.last_error = "Wayback capture blocked by the publisher's robots policy"
            page.next_retry_at = ""
            page.last_check_status = "success"
            return
        except (
            BadGateway,
            TooManyRequests,
            UnknownError,
            WaybackRuntimeError,
            requests.RequestException,
            ArchiveError,
        ) as error:
            message = _safe_error(error, operation="capture")
            self._record_error(page, message, _retry_after(error, self._datetime()))
            raise ArchiveError(f"{page.url}: {message}") from error

        page.archive_status = "pending"
        page.pending_archive_url = normalized
        page.last_submit_at = self._now()
        page.last_error = ""
        page.next_retry_at = ""
        page.attempts = 0

    def _wait_for(self, kind: str) -> None:
        """Apply the configured finite delay before another API request.

        Args:
            kind: Either ``"lookup"`` or ``"capture"``.

        Returns:
            None.

        Examples:
            ``self._wait_for("lookup")`` spaces availability requests.
        """
        delay = self.lookup_delay if kind == "lookup" else self.capture_delay
        previous = self._last_lookup if kind == "lookup" else self._last_capture
        if previous is not None:
            remaining = delay - (self.monotonic() - previous)
            if remaining > 0:
                self.sleep(min(remaining, MAX_RETRY_DELAY.total_seconds()))
        if kind == "lookup":
            self._last_lookup = self.monotonic()
        else:
            self._last_capture = self.monotonic()

    def _now(self) -> str:
        """Return the injected clock value in canonical UTC text.

        Args:
            None.

        Returns:
            ISO 8601 UTC timestamp.

        Examples:
            ``client._now().endswith("Z")`` is True.
        """
        value = self._datetime()
        return value.isoformat().replace("+00:00", "Z")

    def _datetime(self) -> datetime:
        """Read and normalize the injected timezone-aware clock.

        Args:
            None.

        Returns:
            UTC datetime from the injected clock.

        Examples:
            ``client._datetime().tzinfo is UTC`` is True.
        """
        value = self.clock()
        if value.tzinfo is None:
            raise ArchiveError("Wayback clock must return a timezone-aware UTC datetime")
        return value.astimezone(UTC)

    def _record_error(self, page: PageRecord, message: str, retry_after: timedelta | None) -> None:
        """Record a safe transient error and its next permitted retry time.

        Args:
            page: Mutable page record to update.
            message: Sanitized user-visible failure summary.
            retry_after: Optional server-requested retry interval.

        Returns:
            None.

        Examples:
            ``client._record_error(page, "Wayback lookup timed out", None)``.
        """
        page.last_check_at = self._now()
        page.last_check_status = "error"
        page.last_error = message
        page.attempts += 1
        delay = retry_after or timedelta(minutes=min(5 * 2 ** min(page.attempts - 1, 6), 360))
        page.next_retry_at = (self._datetime() + delay).isoformat().replace("+00:00", "Z")


def _availability_snapshot(payload: Any, page_url: str) -> tuple[str, str] | None:
    """Extract a confirmed matching snapshot from an API response.

    Args:
        payload: Decoded Wayback availability response.
        page_url: Requested canonical public page URL.

    Returns:
        Normalized snapshot URL and timestamp, or None when truly absent.

    Examples:
        ``_availability_snapshot({"archived_snapshots": {}}, url)`` is None.
    """
    if not isinstance(payload, dict):
        raise ArchiveError("Wayback returned an invalid availability response")
    snapshots = payload.get("archived_snapshots")
    if not isinstance(snapshots, dict):
        raise ArchiveError("Wayback availability response lacks archived_snapshots")
    if not snapshots:
        return None
    closest = snapshots.get("closest")
    if not isinstance(closest, dict):
        raise ArchiveError("Wayback availability response has an invalid closest snapshot")
    available = closest.get("available")
    status = closest.get("status")
    if type(available) is not bool or not isinstance(status, (int, str)):
        raise ArchiveError("Wayback availability response has invalid availability fields")
    if available is not True or status not in {200, "200"}:
        return None
    timestamp = closest.get("timestamp")
    snapshot_url = closest.get("url")
    if not isinstance(timestamp, str) or not re.fullmatch(r"\d{14}", timestamp):
        raise ArchiveError("Wayback availability response has an invalid timestamp")
    if not _is_wayback_timestamp(timestamp):
        raise ArchiveError("Wayback availability response has an invalid timestamp")
    if not isinstance(snapshot_url, str):
        raise ArchiveError("Wayback availability response has an invalid snapshot URL")
    normalized, path_timestamp = _validate_snapshot(snapshot_url, page_url)
    if path_timestamp != timestamp:
        raise ArchiveError("Wayback availability response has mismatched snapshot timestamps")
    return normalized, timestamp


def _validate_snapshot(snapshot_url: str, page_url: str) -> tuple[str, str]:
    """Validate, normalize, and identify one same-page Wayback snapshot.

    Args:
        snapshot_url: Candidate Wayback snapshot URL.
        page_url: Requested canonical public page URL.

    Returns:
        Normalized HTTPS snapshot URL and its timestamp.

    Examples:
        ``_validate_snapshot(snapshot, "https://palewi.re/")`` validates a snapshot.
    """
    try:
        parsed = urlsplit(snapshot_url)
        port = parsed.port
    except ValueError as error:
        raise ArchiveError("Wayback returned an invalid snapshot URL") from error
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname != "web.archive.org"
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 80 if parsed.scheme == "http" else 443}
        or parsed.query
        or parsed.fragment
    ):
        raise ArchiveError("Wayback returned an invalid snapshot URL")
    match = SNAPSHOT_PATH.fullmatch(parsed.path)
    if not match:
        raise ArchiveError("Wayback returned an invalid snapshot URL")
    timestamp, original = match.groups()
    if not _is_wayback_timestamp(timestamp):
        raise ArchiveError("Wayback returned an invalid snapshot timestamp")
    if not _same_original_url(original, page_url):
        raise ArchiveError("Wayback snapshot does not match the requested page URL")
    return f"https://web.archive.org{parsed.path}", timestamp


def _same_original_url(candidate: str, page_url: str) -> bool:
    """Compare source URLs allowing only HTTP/HTTPS and www equivalents.

    Args:
        candidate: Original URL embedded in a Wayback snapshot.
        page_url: Canonical requested public page URL.

    Returns:
        Whether both URLs represent exactly the same page.

    Examples:
        ``_same_original_url("http://www.palewi.re/", "https://palewi.re/")`` is True.
    """
    try:
        original = urlsplit(candidate)
        page = urlsplit(page_url)
        original_port = original.port
        page_port = page.port
    except ValueError:
        return False
    return (
        original.scheme in {"http", "https"}
        and original.hostname in {"palewi.re", "www.palewi.re"}
        and original.username is None
        and original.password is None
        and original_port in {None, 80 if original.scheme == "http" else 443}
        and not original.query
        and not original.fragment
        and original.path.rstrip("/") == page.path.rstrip("/")
        and original.path.endswith("/") == page.path.endswith("/")
        and page_port is None
    )


def _is_wayback_timestamp(value: str) -> bool:
    """Check whether a 14-digit timestamp is a real calendar date.

    Args:
        value: Candidate ``YYYYMMDDhhmmss`` timestamp.

    Returns:
        Whether the timestamp parses as a real date and time.

    Examples:
        ``_is_wayback_timestamp("20260905120000")`` is True.
    """
    try:
        datetime.strptime(value, "%Y%m%d%H%M%S")
    except ValueError:
        return False
    return True


def _pending_is_fresh(page: PageRecord, now: datetime) -> bool:
    """Determine whether a capture submission remains in its confirmation window.

    Args:
        page: Page record with an optional submission timestamp.
        now: Current UTC time.

    Returns:
        Whether the pending record should not be submitted again yet.

    Examples:
        ``_pending_is_fresh(page, datetime.now(UTC))`` guards repeat saves.
    """
    if not page.last_submit_at:
        return False
    try:
        submitted = datetime.fromisoformat(page.last_submit_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    return submitted + PENDING_COOLDOWN > now


def _require_credentials() -> None:
    """Require both Save Page Now credential environment variables.

    Args:
        None.

    Returns:
        None.

    Examples:
        ``_require_credentials()`` permits authenticated capture work.
    """
    missing = [name for name in ("SAVEPAGENOW_ACCESS_KEY", "SAVEPAGENOW_SECRET_KEY") if not os.environ.get(name)]
    if missing:
        raise ArchiveError(f"{' and '.join(missing)} must be set to create new Wayback captures")


def _retry_after(error: BaseException, now: datetime) -> timedelta | None:
    """Extract a server retry interval without retaining arbitrary headers.

    Args:
        error: Requests or Save Page Now exception.
        now: Current UTC time for HTTP-date conversion.

    Returns:
        Retry interval when a valid header exists, otherwise None.

    Examples:
        ``_retry_after(error, datetime.now(UTC))`` reads ``Retry-After``.
    """
    value = _response_header(error, "Retry-After")
    if not isinstance(value, str):
        return None
    try:
        return max(timedelta(), timedelta(seconds=int(value)))
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
        if retry_at.tzinfo is None:
            return None
        return max(timedelta(), retry_at.astimezone(UTC) - now)


def _response_header(error: BaseException, name: str) -> object | None:
    """Read one named header from supported exception response metadata.

    Args:
        error: Requests or Save Page Now exception.
        name: Header name to retrieve.

    Returns:
        Header value, if safely available.

    Examples:
        ``_response_header(error, "Retry-After")`` returns a retry value.
    """
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    if isinstance(headers, Mapping):
        return headers.get(name)
    if error.args and isinstance(error.args[0], Mapping):
        return error.args[0].get(name)
    return None


def _safe_error(error: BaseException, *, operation: str) -> str:
    """Convert known network exceptions to short non-sensitive status messages.

    Args:
        error: Caught service exception.
        operation: Human-readable failed operation.

    Returns:
        Safe message suitable for a manifest and terminal output.

    Examples:
        ``_safe_error(requests.Timeout(), operation="capture")`` is safe to persist.
    """
    if isinstance(error, TooManyRequests):
        return f"Wayback {operation} was rate limited (HTTP 429)"
    if isinstance(error, BadGateway):
        return f"Wayback {operation} failed (HTTP 502)"
    if isinstance(error, UnknownError):
        return f"Wayback {operation} failed (HTTP 520)"
    if isinstance(error, WaybackRuntimeError):
        return f"Wayback {operation} request failed"
    if isinstance(error, requests.HTTPError):
        response = getattr(error, "response", None)
        status = getattr(response, "status_code", None)
        return (
            f"Wayback {operation} failed (HTTP {status})" if isinstance(status, int) else f"Wayback {operation} failed"
        )
    if isinstance(error, requests.Timeout):
        return f"Wayback {operation} timed out"
    if isinstance(error, requests.ConnectionError):
        return f"Wayback {operation} connection failed"
    if isinstance(error, requests.RequestException):
        return f"Wayback {operation} request failed"
    if isinstance(error, ValueError):
        return f"Wayback {operation} returned invalid JSON"
    return str(error)
