"""Offline tests for Wayback verification and capture state changes."""

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest
import requests
from savepagenow.exceptions import TooManyRequests, WaybackRuntimeError

from scripts.site_archive.manifest import ArchiveError, PageRecord
from scripts.site_archive.wayback import AVAILABILITY_URL, USER_AGENT, WaybackClient

URL = "https://palewi.re/posts/"
STAMP = "20260905120000"
SNAPSHOT = f"https://web.archive.org/web/{STAMP}/https://palewi.re/posts/"
NOW = datetime(2026, 9, 5, 12, 0, tzinfo=UTC)


class Session:
    """Minimal request session returning configured responses or exceptions."""

    def __init__(self, result: requests.Response | BaseException | list[requests.Response | BaseException]):
        """Set one or more responses returned from requests.

        Args:
            result: Response, exception, or ordered responses and exceptions to return.

        Returns:
            None.

        Examples:
            ``Session(response({"archived_snapshots": {}}))`` reports absent data.
        """
        self.results = list(result) if isinstance(result, list) else [result]
        self.calls: list[tuple[str, dict[str, object]]] = []

    def get(self, url: str, **kwargs: object) -> requests.Response:
        """Record and return one availability response.

        Args:
            url: Requested endpoint.
            **kwargs: Request options.

        Returns:
            Configured response.

        Examples:
            The client requests the documented availability endpoint.
        """
        self.calls.append((url, kwargs))
        result = self.results.pop(0)
        if isinstance(result, BaseException):
            raise result
        if not isinstance(result, requests.Response):
            raise AssertionError("Session result must be a requests response")
        return result


def response(
    payload: object,
    status: int = 200,
    retry_after: str | None = None,
    content_type: str | None = None,
) -> requests.Response:
    """Build an in-memory JSON response.

    Args:
        payload: JSON value to return.
        status: HTTP status code.
        retry_after: Optional Retry-After header.
        content_type: Optional response MIME type.

    Returns:
        Configured requests response.

    Examples:
        ``response({"archived_snapshots": {}})`` represents no snapshot.
    """
    result = requests.Response()
    result.status_code = status
    result.url = AVAILABILITY_URL
    result._content = payload.encode() if isinstance(payload, str) else json.dumps(payload).encode()
    result._content_consumed = True
    if retry_after:
        result.headers["Retry-After"] = retry_after
    if content_type:
        result.headers["Content-Type"] = content_type
    return result


def client(
    result: requests.Response | BaseException,
    *,
    capture_page: Callable[..., str] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> WaybackClient:
    """Create a deterministic client around one fake availability response.

    Args:
        result: Availability result.
        capture_page: Optional capture replacement.
        sleep: Optional delay replacement.

    Returns:
        Configured client.

    Examples:
        ``client(response({"archived_snapshots": {}}))``.
    """
    return WaybackClient(
        session=Session(result),
        capture_page=capture_page if capture_page is not None else lambda **kwargs: SNAPSHOT,
        clock=lambda: NOW,
        sleep=sleep if sleep is not None else lambda seconds: None,
    )


def test_verify_confirms_only_matching_valid_snapshots() -> None:
    """Record a valid same-page snapshot as confirmed archive evidence.

    Args:
        None.

    Returns:
        None.

    Examples:
        HTTP and www source equivalents are accepted for the same page.
    """
    page = PageRecord(url=URL, live_status="live")
    snapshot = f"http://web.archive.org/web/{STAMP}/http://www.palewi.re/posts/"
    archive = client(
        response(
            {"archived_snapshots": {"closest": {"available": True, "status": 200, "timestamp": STAMP, "url": snapshot}}}
        )
    )
    archive.verify(page)
    assert page.archive_status == "archived"
    assert page.archive_url == snapshot.replace("http://", "https://", 1)
    assert page.snapshot_at == STAMP
    assert page.last_verified_at == "2026-09-05T12:00:00Z"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"archived_snapshots": {"closest": {"available": [], "status": "200"}}},
        {"archived_snapshots": {"closest": {"available": False, "status": {}}}},
        {"archived_snapshots": {"closest": {"available": True, "status": "200", "timestamp": "bad", "url": SNAPSHOT}}},
        {
            "archived_snapshots": {
                "closest": {
                    "available": True,
                    "status": "200",
                    "timestamp": STAMP,
                    "url": f"https://web.archive.org/web/{STAMP}/https://palewi.re/other/",
                }
            }
        },
    ],
)
def test_verify_rejects_malformed_and_wrong_url_snapshots(payload: object) -> None:
    """Treat malformed availability evidence as an error, never as missing.

    Args:
        payload: Invalid API payload.

    Returns:
        None.

    Examples:
        An absent ``archived_snapshots`` mapping is malformed.
    """
    page = PageRecord(url=URL, live_status="live")
    with pytest.raises(ArchiveError, match="Wayback"):
        client(response(payload)).verify(page)
    assert page.archive_status == "unknown"
    assert page.last_check_status == "error"
    assert page.next_retry_at


def test_verify_empty_mapping_is_missing_but_retains_fresh_pending_capture() -> None:
    """Allow Save Page Now time to process before a capture is resubmitted.

    Args:
        None.

    Returns:
        None.

    Examples:
        Empty snapshot data changes an ordinary record to missing.
    """
    ordinary = PageRecord(url=URL, live_status="live")
    client(response({"archived_snapshots": {}})).verify(ordinary)
    assert ordinary.archive_status == "missing"
    assert ordinary.last_check_status == "success"

    pending = PageRecord(
        url=URL,
        live_status="live",
        archive_status="pending",
        pending_archive_url=SNAPSHOT,
        last_submit_at=(NOW - timedelta(hours=1)).isoformat(),
    )
    client(response({"archived_snapshots": {}})).verify(pending)
    assert pending.archive_status == "pending"
    assert pending.pending_archive_url == SNAPSHOT


def test_verify_accepts_proven_trailing_slash_snapshot_alias() -> None:
    """Confirm an alias snapshot only when both live pages name one canonical URL.

    Args:
        None.

    Returns:
        None.

    Examples:
        A snapshot of ``/week-1`` can confirm the canonical ``/week-1/`` page.
    """
    requested = "https://palewi.re/docs/coding-the-news/scripts/week-1/"
    alias = requested.rstrip("/")
    snapshot = f"http://web.archive.org/web/{STAMP}/{alias}"
    canonical_link = f'<link rel="canonical" href="{requested}">'
    session = Session(
        [
            response(
                {
                    "archived_snapshots": {
                        "closest": {"available": True, "status": 200, "timestamp": STAMP, "url": snapshot}
                    }
                }
            ),
            response(canonical_link, content_type="text/html"),
            response(canonical_link, content_type="text/html"),
        ]
    )
    page = PageRecord(url=requested, live_status="live")
    WaybackClient(session=session, clock=lambda: NOW, sleep=lambda seconds: None).verify(page)
    assert page.archive_status == "archived"
    assert page.archive_url == snapshot.replace("http://", "https://", 1)
    assert [url for url, _ in session.calls] == [AVAILABILITY_URL, requested, alias]


@pytest.mark.parametrize(
    "alias_html",
    [
        "<p>No canonical link</p>",
        '<link rel="canonical" href="https://palewi.re/docs/coding-the-news/scripts/week-2/">',
    ],
)
def test_verify_rejects_unproven_trailing_slash_snapshot_alias(alias_html: str) -> None:
    """Reject a slash alias unless both live pages prove the requested canonical.

    Args:
        alias_html: Alias page HTML without the requested sole canonical link.

    Returns:
        None.

    Examples:
        A missing or unrelated canonical link keeps a snapshot unconfirmed.
    """
    requested = "https://palewi.re/docs/coding-the-news/scripts/week-1/"
    alias = requested.rstrip("/")
    snapshot = f"https://web.archive.org/web/{STAMP}/{alias}"
    session = Session(
        [
            response(
                {
                    "archived_snapshots": {
                        "closest": {"available": True, "status": 200, "timestamp": STAMP, "url": snapshot}
                    }
                }
            ),
            response(f'<link rel="canonical" href="{requested}">', content_type="text/html"),
            response(alias_html, content_type="text/html"),
        ]
    )
    page = PageRecord(url=requested, live_status="live")
    with pytest.raises(ArchiveError, match="canonical"):
        WaybackClient(session=session, clock=lambda: NOW, sleep=lambda seconds: None).verify(page)
    assert page.archive_status == "unknown"
    assert page.last_check_status == "error"


def test_verify_throttle_honors_retry_after_and_preserves_archived_evidence() -> None:
    """Keep earlier valid archives when a later service request is throttled.

    Args:
        None.

    Returns:
        None.

    Examples:
        A 429 response records its Retry-After cooldown.
    """
    page = PageRecord(
        url=URL,
        live_status="live",
        archive_status="archived",
        archive_url=SNAPSHOT,
        snapshot_at=STAMP,
    )
    with pytest.raises(ArchiveError, match="availability check failed"):
        client(response({}, status=429, retry_after="120")).verify(page)
    assert page.archive_status == "archived"
    assert page.archive_url == SNAPSHOT
    assert page.last_check_status == "error"
    assert page.next_retry_at == "2026-09-05T12:02:00Z"


def test_capture_requires_credentials_before_network_work(monkeypatch: pytest.MonkeyPatch) -> None:
    """Record missing Save Page Now credentials as resumable state.

    Args:
        monkeypatch: Removes environment credentials.

    Returns:
        None.

    Examples:
        Capture does not perform its confirming lookup without credentials.
    """
    monkeypatch.delenv("SAVEPAGENOW_ACCESS_KEY", raising=False)
    monkeypatch.delenv("SAVEPAGENOW_SECRET_KEY", raising=False)
    session = Session(response({"archived_snapshots": {}}))
    page = PageRecord(url=URL, live_status="live", archive_status="missing")
    with pytest.raises(ArchiveError, match="SAVEPAGENOW_ACCESS_KEY"):
        WaybackClient(session=session, clock=lambda: NOW).capture(page)
    assert not session.calls
    assert page.last_check_status == "error"
    assert page.next_retry_at


def test_capture_rechecks_then_records_pending_and_respects_rate_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    """Submit only after a fresh absence check and require later verification.

    Args:
        monkeypatch: Supplies capture credentials.

    Returns:
        None.

    Examples:
        A returned Save Page Now URL remains pending, not archived.
    """
    monkeypatch.setenv("SAVEPAGENOW_ACCESS_KEY", "key")
    monkeypatch.setenv("SAVEPAGENOW_SECRET_KEY", "secret")
    captured: list[dict[str, object]] = []

    def submit(url: str, **kwargs: object) -> str:
        """Return a pending snapshot URL.

        Args:
            url: Submitted page URL.
            **kwargs: Save Page Now options.

        Returns:
            Pending snapshot URL.

        Examples:
            The submission is authenticated and permits cache results.
        """
        assert url == URL
        captured.append(kwargs)
        return SNAPSHOT

    page = PageRecord(url=URL, live_status="live", archive_status="missing")
    archive = client(response({"archived_snapshots": {}}), capture_page=submit)
    archive.capture(page)
    assert page.archive_status == "pending"
    assert page.pending_archive_url == SNAPSHOT
    assert page.archive_url == ""
    assert page.last_submit_at == "2026-09-05T12:00:00Z"
    assert captured == [
        {
            "user_agent": USER_AGENT,
            "accept_cache": True,
            "timeout": 120,
            "authenticate": True,
        }
    ]


def test_lookup_and_capture_timeouts_are_separate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Use dedicated timeouts for availability checks and capture submissions.

    Args:
        monkeypatch: Supplies capture credentials.

    Returns:
        None.

    Examples:
        A short availability timeout does not shorten a slow capture request.
    """
    monkeypatch.setenv("SAVEPAGENOW_ACCESS_KEY", "key")
    monkeypatch.setenv("SAVEPAGENOW_SECRET_KEY", "secret")
    submitted: list[dict[str, object]] = []
    session = Session(response({"archived_snapshots": {}}))
    page = PageRecord(url=URL, live_status="live", archive_status="missing")

    def submit(url: str, **kwargs: object) -> str:
        """Record the Save Page Now options used for one capture.

        Args:
            url: Submitted page URL.
            **kwargs: Save Page Now options.

        Returns:
            Pending snapshot URL.

        Examples:
            A capture uses the configured capture timeout.
        """
        assert url == URL
        submitted.append(kwargs)
        return SNAPSHOT

    archive = WaybackClient(
        timeout=7.5,
        capture_timeout=80.9,
        session=session,
        capture_page=submit,
        clock=lambda: NOW,
        sleep=lambda seconds: None,
    )
    archive.capture(page)
    assert session.calls[0][1]["timeout"] == 7.5
    assert submitted[0]["timeout"] == 80


def test_capture_accepts_proven_trailing_slash_snapshot_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    """Save a proven trailing-slash alias as a pending capture result.

    Args:
        monkeypatch: Supplies capture credentials.

    Returns:
        None.

    Examples:
        A ``/week-1`` response remains pending for canonical ``/week-1/``.
    """
    monkeypatch.setenv("SAVEPAGENOW_ACCESS_KEY", "key")
    monkeypatch.setenv("SAVEPAGENOW_SECRET_KEY", "secret")
    requested = "https://palewi.re/docs/coding-the-news/scripts/week-1/"
    alias = requested.rstrip("/")
    snapshot = f"https://web.archive.org/web/{STAMP}/{alias}"
    canonical_link = f'<link rel="canonical" href="{requested}">'
    session = Session(
        [
            response({"archived_snapshots": {}}),
            response(canonical_link, content_type="text/html"),
            response(canonical_link, content_type="text/html"),
        ]
    )
    page = PageRecord(url=requested, live_status="live", archive_status="missing")
    WaybackClient(
        session=session,
        capture_page=lambda url, **kwargs: snapshot,
        clock=lambda: NOW,
        sleep=lambda seconds: None,
    ).capture(page)
    assert page.archive_status == "pending"
    assert page.pending_archive_url == snapshot


def test_capture_keeps_response_headers_and_bodies_out_of_error_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Store safe capture failures while retaining retry information.

    Args:
        monkeypatch: Supplies capture credentials.

    Returns:
        None.

    Examples:
        A rate-limit response contributes only its bounded Retry-After value.
    """
    monkeypatch.setenv("SAVEPAGENOW_ACCESS_KEY", "key")
    monkeypatch.setenv("SAVEPAGENOW_SECRET_KEY", "secret")
    page = PageRecord(url=URL, live_status="live", archive_status="missing")

    def throttled(url: str, **kwargs: object) -> str:
        """Raise an exception with sensitive response headers.

        Args:
            url: Submitted page URL.
            **kwargs: Unused Save Page Now options.

        Returns:
            Never returns.

        Examples:
            Save Page Now places headers in ``TooManyRequests.args``.
        """
        raise TooManyRequests({"Retry-After": "120", "Set-Cookie": "secret-cookie"})

    with pytest.raises(ArchiveError, match="rate limited"):
        client(response({"archived_snapshots": {}}), capture_page=throttled).capture(page)
    assert page.last_error == "Wayback capture was rate limited (HTTP 429)"
    assert "secret-cookie" not in page.last_error
    assert page.next_retry_at == "2026-09-05T12:02:00Z"

    opaque = PageRecord(url=URL, live_status="live", archive_status="missing")

    def malformed_response(url: str, **kwargs: object) -> str:
        """Raise an opaque Wayback error with a response-like body.

        Args:
            url: Submitted page URL.
            **kwargs: Unused Save Page Now options.

        Returns:
            Never returns.

        Examples:
            Missing capture location errors must not write raw API payloads.
        """
        raise WaybackRuntimeError({"headers": {"Set-Cookie": "secret-cookie"}, "content": b"private body"})

    with pytest.raises(ArchiveError, match="capture request failed"):
        client(response({"archived_snapshots": {}}), capture_page=malformed_response).capture(opaque)
    assert opaque.last_error == "Wayback capture request failed"
    assert "private body" not in opaque.last_error


def test_capture_timeout_stays_pending_before_later_verification(monkeypatch: pytest.MonkeyPatch) -> None:
    """Treat a lost capture response as potentially accepted by Wayback.

    Args:
        monkeypatch: Supplies capture credentials.

    Returns:
        None.

    Examples:
        A later availability lookup, rather than another submit, resolves a timeout.
    """
    monkeypatch.setenv("SAVEPAGENOW_ACCESS_KEY", "key")
    monkeypatch.setenv("SAVEPAGENOW_SECRET_KEY", "secret")
    page = PageRecord(url=URL, live_status="live", archive_status="missing")

    def lost_response(url: str, **kwargs: object) -> str:
        """Simulate a capture request whose response is lost.

        Args:
            url: Submitted page URL.
            **kwargs: Unused Save Page Now options.

        Returns:
            Never returns.

        Examples:
            A timeout does not prove that Wayback rejected the capture.
        """
        raise requests.Timeout("private upstream response")

    with pytest.raises(ArchiveError, match="capture timed out"):
        client(response({"archived_snapshots": {}}), capture_page=lost_response).capture(page)
    assert page.archive_status == "pending"
    assert page.pending_archive_url == ""
    assert page.last_submit_at == "2026-09-05T12:00:00Z"
    assert page.last_check_status == "error"
    assert page.last_error == "Wayback capture timed out"
