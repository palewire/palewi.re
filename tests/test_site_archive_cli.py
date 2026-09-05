"""Offline tests for the site archive commands."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from scripts.site_archive import cli as archive_cli
from scripts.site_archive.cli import ArchiveRun, cli, report_text
from scripts.site_archive.manifest import ArchiveError, Manifest, ManifestStore
from scripts.site_archive.wayback import WaybackClient

URL = "https://palewi.re/posts/"


def seed_manifest(path: Path, status: str = "unknown") -> Manifest:
    """Create one live page in a local manifest.

    Args:
        path: Destination manifest.
        status: Initial archive status.

    Returns:
        The saved manifest.

    Examples:
        ``seed_manifest(path)`` creates one unchecked live page.
    """
    state = Manifest()
    page = state.page(URL)
    page.live_status = "live"
    page.archive_status = status
    if status == "pending":
        page.last_submit_at = "2026-01-01T00:00:00Z"
        page.pending_archive_url = f"https://web.archive.org/web/20260101000000/{URL}"
    ManifestStore(path).save(state)
    return state


def test_report_is_offline_and_honest(tmp_path: Path) -> None:
    """Report pending and unknown pages without claiming complete coverage.

    Args:
        tmp_path: State directory.

    Returns:
        None.

    Examples:
        Pending snapshots count separately from confirmed archives.
    """
    path = tmp_path / "manifest.json"
    state = seed_manifest(path, "pending")
    state.discovery_queue = [URL]
    ManifestStore(path).save(state)
    result = CliRunner().invoke(cli, ["report", "--manifest", str(path)])
    assert result.exit_code == 0
    assert "| Confirmed archives | 0 |" in result.output
    assert "| Pending capture confirmations | 1 |" in result.output
    assert "unfinished or has gaps" in result.output
    assert "does not guarantee" in result.output


@pytest.mark.parametrize("command", ["report", "verify", "capture", "discover", "sync"])
def test_corrupt_manifest_is_not_overwritten(tmp_path: Path, command: str) -> None:
    """Fail all commands on corrupt persisted data.

    Args:
        tmp_path: State directory.
        command: Command to run.

    Returns:
        None.

    Examples:
        No command replaces a broken manifest with a new empty document.
    """
    path = tmp_path / "manifest.json"
    path.write_text("broken")
    result = CliRunner().invoke(cli, [command, "--manifest", str(path)])
    assert result.exit_code != 0
    assert path.read_text() == "broken"


def test_verify_orders_unchecked_pages_and_preserves_failures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Checkpoint a failing check and leave other candidates for later.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces Wayback requests.

    Returns:
        None.

    Examples:
        Rate limiting stops the batch without losing the failed record.
    """
    path = tmp_path / "state.json"
    state = seed_manifest(path)
    state.page("https://palewi.re/old/").live_status = "live"
    state.pages["https://palewi.re/old/"].last_check_at = "2020-01-01T00:00:00+00:00"
    ManifestStore(path).save(state)

    def fail(_client: WaybackClient, page: archive_cli.PageRecord) -> None:
        """Record an API error.

        Args:
            _client: Unused client.
            page: Candidate record.

        Returns:
            Never returns.

        Examples:
            Simulates a rate-limited lookup.
        """
        assert page.url == URL
        page.last_check_status = "error"
        page.last_error = "Rate limited"
        raise ArchiveError("Rate limited")

    monkeypatch.setattr(WaybackClient, "verify", fail)
    report = tmp_path / "report.md"
    result = CliRunner().invoke(cli, ["verify", "--manifest", str(path), "--summary", str(report)])
    assert result.exit_code != 0
    assert ManifestStore(path).load().pages[URL].last_error == "Rate limited"
    assert report.is_file()
    assert "| Archive checks with errors | 1 |" in report.read_text()


def test_verify_prioritizes_due_pending_confirmations(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Check pending confirmations before the unverified discovery backlog.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces Wayback requests.

    Returns:
        None.

    Examples:
        A due pending capture is checked even when unknown pages exist.
    """
    path = tmp_path / "state.json"
    state = seed_manifest(path)
    pending = state.page("https://palewi.re/pending/")
    pending.live_status = "live"
    pending.archive_status = "pending"
    pending.last_submit_at = "2026-01-01T00:00:00Z"
    deferred = state.page("https://palewi.re/deferred/")
    deferred.live_status = "live"
    deferred.archive_status = "pending"
    deferred.last_submit_at = "2026-01-01T00:00:00Z"
    deferred.next_retry_at = "2099-01-01T00:00:00+00:00"
    ManifestStore(path).save(state)
    calls: list[str] = []

    def verify(_client: WaybackClient, page: archive_cli.PageRecord) -> None:
        """Record each selected confirmation candidate.

        Args:
            _client: Unused client.
            page: Selected page record.

        Returns:
            None.

        Examples:
            The first candidate is the due pending page.
        """
        calls.append(page.url)

    monkeypatch.setattr(WaybackClient, "verify", verify)
    ArchiveRun(path).verify(1, float("inf"))
    assert calls == [pending.url]


def test_capture_limits_and_retry_dates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Select due missing pages and exclude pending, blocked, and non-live pages.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces capture calls.

    Returns:
        None.

    Examples:
        A future retry date keeps a missing page out of this batch.
    """
    path = tmp_path / "state.json"
    monkeypatch.setattr(ArchiveRun, "check_live", lambda *args: True)
    state = seed_manifest(path, "missing")
    for slug, status in [("pending", "pending"), ("blocked", "blocked"), ("later", "missing")]:
        page = state.page(f"https://palewi.re/{slug}/")
        page.archive_status = status
        page.live_status = "live"
        if status == "pending":
            page.last_submit_at = "2026-01-01T00:00:00Z"
            page.pending_archive_url = f"https://web.archive.org/web/20260101000000/{page.url}"
    state.pages["https://palewi.re/later/"].next_retry_at = "2099-01-01T00:00:00+00:00"
    state.page("https://palewi.re/not-live/").archive_status = "missing"
    ManifestStore(path).save(state)
    calls: list[str] = []

    def capture(_client: WaybackClient, page: archive_cli.PageRecord) -> None:
        """Record a candidate capture.

        Args:
            _client: Unused client.
            page: Candidate page.

        Returns:
            None.

        Examples:
            The candidate becomes pending, not confirmed.
        """
        calls.append(page.url)
        page.archive_status = "pending"
        page.last_submit_at = "2026-01-01T00:00:00Z"
        page.pending_archive_url = f"https://web.archive.org/web/20260101000000/{page.url}"

    monkeypatch.setattr(WaybackClient, "capture", capture)
    result = CliRunner().invoke(cli, ["capture", "--manifest", str(path), "--max-captures", "1"])
    assert result.exit_code == 0
    assert calls == [URL]
    assert ManifestStore(path).load().pages[URL].archive_status == "pending"


def test_capture_failure_saves_summary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Surface configuration failures while keeping the candidate.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces capture requests.

    Returns:
        None.

    Examples:
        Missing credentials are not reported as successful captures.
    """
    path = tmp_path / "state.json"
    monkeypatch.setattr(ArchiveRun, "check_live", lambda *args: True)
    seed_manifest(path, "missing")

    def fail(_client: WaybackClient, page: archive_cli.PageRecord) -> None:
        """Reject a capture without credentials.

        Args:
            _client: Unused client.
            page: Capture candidate.

        Returns:
            Never returns.

        Examples:
            Used to simulate an unconfigured local run.
        """
        page.last_error = "Credentials missing"
        page.last_check_status = "error"
        raise ArchiveError(page.last_error)

    monkeypatch.setattr(WaybackClient, "capture", fail)
    result = CliRunner().invoke(cli, ["capture", "--manifest", str(path)])
    assert result.exit_code != 0
    assert "Credentials missing" in result.output
    assert ManifestStore(path).load().pages[URL].archive_status == "missing"


def test_sync_lookup_only_and_discover_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run discovery and lookups without captures.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces network-facing phases.

    Returns:
        None.

    Examples:
        Lookup-only sync must not invoke the capture phase.
    """
    path = tmp_path / "state.json"
    phases: list[str] = []
    monkeypatch.setattr(archive_cli, "build_seeds", lambda build: [URL])

    def discover(runner: archive_cli.PageDiscovery, seeds: list[str], *, limit: int, deadline: float) -> int:
        """Add a discovered fixture page.

        Args:
            runner: Discovery instance.
            seeds: Requested seeds.
            limit: Request limit.
            deadline: End time.

        Returns:
            One attempted request.

        Examples:
            Replaces the live crawl during a CLI test.
        """
        assert seeds == [URL]
        assert limit > 0 and deadline > 0
        phases.append("discover")
        runner.manifest.page(URL).live_status = "live"
        return 1

    monkeypatch.setattr(archive_cli.PageDiscovery, "run", discover)
    monkeypatch.setattr(ArchiveRun, "verify", lambda *args: phases.append("verify"))
    monkeypatch.setattr(ArchiveRun, "capture", lambda *args: phases.append("capture"))
    result = CliRunner().invoke(cli, ["sync", "--manifest", str(path), "--lookup-only"])
    assert result.exit_code == 0
    assert phases == ["discover", "verify"]
    phases.clear()
    result = CliRunner().invoke(cli, ["sync", "--manifest", str(path)])
    assert result.exit_code == 0
    assert phases == ["discover", "verify", "capture"]
    phases.clear()
    result = CliRunner().invoke(cli, ["discover", "--manifest", str(path)])
    assert result.exit_code == 0
    assert phases == ["discover"]


def test_missing_build_saves_error_report(tmp_path: Path) -> None:
    """Save a report even when discovery cannot start.

    Args:
        tmp_path: State directory.

    Returns:
        None.

    Examples:
        A missing build is an actionable failure, not an empty inventory success.
    """
    path = tmp_path / "state.json"
    summary = tmp_path / "report.md"
    result = CliRunner().invoke(
        cli,
        ["discover", "--manifest", str(path), "--build-dir", str(tmp_path / "absent"), "--summary", str(summary)],
    )
    assert result.exit_code != 0
    assert "make bake" in result.output
    assert summary.is_file()


def test_deadlines_prevent_new_archive_requests(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Stop work before making a request when the time budget is spent.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces the client with a request counter.

    Returns:
        None.

    Examples:
        Neither verify nor capture runs after its deadline.
    """
    path = tmp_path / "state.json"
    seed_manifest(path, "missing")
    calls: list[str] = []
    monkeypatch.setattr(WaybackClient, "verify", lambda *args: calls.append("verify"))
    monkeypatch.setattr(WaybackClient, "capture", lambda *args: calls.append("capture"))
    run = ArchiveRun(path)
    run.verify(1, 0)
    run.capture(1, 0)
    assert not calls


def test_report_escapes_errors_and_limits_problem_list() -> None:
    """Keep external error text readable and prevent HTML in summaries.

    Args:
        None.

    Returns:
        None.

    Examples:
        Long error lists refer readers to the manifest.
    """
    state = Manifest()
    for index in range(51):
        state.discovery_errors[f"https://palewi.re/{index}/"] = "<b>failed</b>"
    text = report_text(state)
    assert "<b>" not in text
    assert "&lt;b&gt;" in text
    assert "1 more problems" in text


def test_lookup_failure_stops_capture_phase(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not submit captures after availability checks fail.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces network-facing client methods.

    Returns:
        None.

    Examples:
        A service outage results in one failed lookup and no capture.
    """
    path = tmp_path / "state.json"
    seed_manifest(path, "missing")
    calls: list[str] = []

    def fail(_client: WaybackClient, page: archive_cli.PageRecord) -> None:
        """Record a service failure.

        Args:
            _client: Unused client.
            page: Lookup candidate.

        Returns:
            Never returns.

        Examples:
            Simulates an unavailable Wayback API.
        """
        page.last_check_status = "error"
        raise ArchiveError("Service unavailable")

    monkeypatch.setattr(WaybackClient, "verify", fail)
    monkeypatch.setattr(WaybackClient, "capture", lambda *args: calls.append("capture"))
    run = ArchiveRun(path)
    run.verify(1, float("inf"))
    run.capture(1, float("inf"))
    assert run.wayback_failed
    assert not calls


def test_capture_checkpoints_before_submission(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Persist pending state before a capture can be interrupted.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces lookup and credentials.

    Returns:
        None.

    Examples:
        An interrupted network request leaves a pending record on disk.
    """
    path = tmp_path / "state.json"
    state = seed_manifest(path, "missing")
    store = ManifestStore(path)
    monkeypatch.setenv("SAVEPAGENOW_ACCESS_KEY", "test")
    monkeypatch.setenv("SAVEPAGENOW_SECRET_KEY", "test")
    monkeypatch.setattr(WaybackClient, "verify", lambda *args: None)

    def interrupted(url: str, **kwargs: object) -> str:
        """Interrupt a request after checking durable state.

        Args:
            url: Capture target.
            **kwargs: Capture options.

        Returns:
            Never returns.

        Examples:
            Represents a process interrupted during submission.
        """
        saved = store.load().pages[url]
        assert saved.archive_status == "pending"
        assert saved.last_submit_at
        raise KeyboardInterrupt

    client = WaybackClient(capture_page=interrupted, checkpoint=lambda: store.save(state))
    with pytest.raises(KeyboardInterrupt):
        client.capture(state.pages[URL])
    assert store.load().pages[URL].archive_status == "pending"


@pytest.mark.parametrize("live_status", ["live", "missing", "error"])
def test_capture_rechecks_public_page(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, live_status: str) -> None:
    """Do not archive a removed or inaccessible page based on an old live check.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces live requests and capture submission.
        live_status: Result of the new live-page request.

    Returns:
        None.

    Examples:
        A newly missing page stops before the capture API is called.
    """
    path = tmp_path / "state.json"
    seed_manifest(path, "missing")
    calls: list[str] = []

    def visit(discovery: archive_cli.PageDiscovery, url: str) -> None:
        """Simulate the current public page response.

        Args:
            discovery: Discovery instance.
            url: Requested page.

        Returns:
            None.

        Examples:
            A failed request raises an explicit error.
        """
        if live_status == "error":
            raise ArchiveError("Page request failed")
        discovery.manifest.pages[url].live_status = live_status

    monkeypatch.setattr(archive_cli.PageDiscovery, "visit", visit)
    monkeypatch.setattr(WaybackClient, "capture", lambda *args: calls.append("capture"))
    run = ArchiveRun(path)
    run.capture(1, float("inf"))
    assert calls == (["capture"] if live_status == "live" else [])
    assert ManifestStore(path).load().pages[URL].live_status == live_status
    assert bool(run.failures) is (live_status != "live")
