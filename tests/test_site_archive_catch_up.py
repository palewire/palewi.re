"""Offline tests for durable site-archive catch-up control."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from scripts.site_archive import catch_up
from scripts.site_archive.branch import DEFAULT_BRANCH, DEFAULT_REPOSITORY
from scripts.site_archive.manifest import Manifest, ManifestStore

NOW = datetime(2026, 9, 6, 12, 0, tzinfo=UTC)
DIGEST = "a" * 64


def state_with_dispatch() -> catch_up.CatchUpState:
    """Create an active state waiting for one dispatched archive run.

    Returns:
        Controller state with valid in-flight dispatch fields.

    Examples:
        ``state_with_dispatch().dispatch_token`` is a GitHub run ID.
    """
    return catch_up.CatchUpState(
        active=True,
        phase="lookup",
        dispatch_token="123",
        dispatched_at="2026-09-06T12:00:00Z",
        next_retry_at="2026-09-06T12:15:00Z",
        before_manifest_sha256=DIGEST,
    )


def live_page(manifest: Manifest, status: str, path: str = "posts") -> None:
    """Add one due live archive record to a manifest.

    Args:
        manifest: Mutable archive manifest.
        status: Archive status for the page.
        path: URL path component used to make the page unique.

    Returns:
        None.

    Examples:
        ``live_page(manifest, "missing")`` creates a capture candidate.
    """
    page = manifest.page(f"https://palewi.re/{path}/")
    page.live_status = "live"
    page.archive_status = status


def test_start_stop_and_resume_reset_controller_state() -> None:
    """Require explicit start or resume after a stopped or blocked state.

    Args:
        None.

    Returns:
        None.

    Examples:
        Start always chooses known missing capture work first.
    """
    state = catch_up.CatchUpState(active=False, phase="blocked", last_error="Archive failed", no_progress_runs=2)
    resumed = catch_up.start(state)
    assert resumed.active is True
    assert resumed.phase == "capture"
    assert resumed.last_error == ""
    assert resumed.no_progress_runs == 0
    stopped = catch_up.stop(resumed, NOW)
    assert stopped.active is False
    assert stopped.phase == "complete"
    assert stopped.finished_at == "2026-09-06T12:00:00Z"


def test_capture_is_selected_before_lookup_and_only_once() -> None:
    """Dispatch known missing pages first and retain an in-flight marker.

    Args:
        None.

    Returns:
        None.

    Examples:
        A second tick cannot duplicate the same capture dispatch.
    """
    manifest = Manifest()
    live_page(manifest, "missing")
    state = catch_up.start(catch_up.CatchUpState())
    decision = catch_up.decide(
        state,
        manifest,
        now=NOW,
        workflow_run=None,
        manifest_sha256=DIGEST,
        controller_run_id="456",
    )
    assert decision.action == "capture"
    assert state.phase == "lookup"
    assert state.dispatch_token == "456"
    waiting = catch_up.decide(
        state,
        manifest,
        now=NOW + timedelta(minutes=1),
        workflow_run=None,
        manifest_sha256=DIGEST,
        controller_run_id="789",
    )
    assert waiting.action == "wait"
    assert state.dispatch_token == "456"


def test_completed_capture_selects_lookup_before_another_capture() -> None:
    """Alternate a completed capture batch with discovery and verification.

    Args:
        None.

    Returns:
        None.

    Examples:
        A changed manifest clears the no-progress counter.
    """
    manifest = Manifest(discovery_queue=["https://palewi.re/sitemap.xml"])
    state = state_with_dispatch()
    decision = catch_up.decide(
        state,
        manifest,
        now=NOW + timedelta(minutes=1),
        workflow_run=catch_up.WorkflowRun(99, "completed", "success"),
        manifest_sha256="b" * 64,
        controller_run_id="456",
    )
    assert decision.action == "lookup"
    assert state.dispatch_token == "456"
    assert state.phase == "capture"


def test_pending_capture_waits_for_the_full_confirmation_window() -> None:
    """Avoid a premature lookup or repeat capture for a fresh pending page.

    Args:
        None.

    Returns:
        None.

    Examples:
        A pending capture becomes eligible exactly after 24 hours.
    """
    manifest = Manifest()
    live_page(manifest, "pending")
    page = next(iter(manifest.pages.values()))
    page.last_submit_at = "2026-09-06T11:00:00Z"
    state = catch_up.start(catch_up.CatchUpState())
    decision = catch_up.decide(
        state,
        manifest,
        now=NOW,
        workflow_run=None,
        manifest_sha256=DIGEST,
        controller_run_id="456",
    )
    assert decision.action == "wait"
    assert state.next_retry_at == "2026-09-07T11:00:00Z"


def test_failed_or_missing_dispatched_runs_pause_controller() -> None:
    """Pause instead of retrying a failed or unavailable Actions batch.

    Args:
        None.

    Returns:
        None.

    Examples:
        A failed archive job requires an explicit resume.
    """
    manifest = Manifest()
    state = state_with_dispatch()
    failed = catch_up.decide(
        state,
        manifest,
        now=NOW,
        workflow_run=catch_up.WorkflowRun(12, "completed", "failure"),
        manifest_sha256=DIGEST,
        controller_run_id="456",
    )
    assert failed.action == "blocked"
    assert state.active is False
    assert "ended with failure" in state.last_error

    state = state_with_dispatch()
    missing = catch_up.decide(
        state,
        manifest,
        now=NOW + timedelta(minutes=16),
        workflow_run=None,
        manifest_sha256=DIGEST,
        controller_run_id="456",
    )
    assert missing.action == "blocked"
    assert "did not appear" in state.last_error


@pytest.mark.parametrize(
    "error",
    [
        "Wayback capture request failed",
        "Wayback capture connection failed",
    ],
)
def test_partial_transient_failure_waits_then_automatically_resumes(error: str) -> None:
    """Keep catch-up active after a persisted partial Wayback service failure.

    Args:
        None.

    Returns:
        None.

    Examples:
        A returned pending snapshot counts as progress, unlike an empty pending marker.
    """
    manifest = Manifest()
    live_page(manifest, "pending", "captured")
    captured = manifest.pages["https://palewi.re/captured/"]
    captured.pending_archive_url = "https://web.archive.org/web/20260906120000/https://palewi.re/captured/"
    captured.last_submit_at = "2026-09-06T12:00:00Z"
    live_page(manifest, "pending", "ambiguous")
    ambiguous = manifest.pages["https://palewi.re/ambiguous/"]
    ambiguous.last_submit_at = "2026-09-06T12:00:00Z"
    ambiguous.last_check_status = "error"
    ambiguous.last_error = error
    ambiguous.next_retry_at = "2026-09-06T12:03:00Z"
    state = state_with_dispatch()
    state.before_archive_progress = 0
    waiting = catch_up.decide(
        state,
        manifest,
        now=NOW,
        workflow_run=catch_up.WorkflowRun(12, "completed", "failure"),
        manifest_sha256="b" * 64,
        controller_run_id="456",
    )
    assert waiting.action == "wait"
    assert state.active is True
    assert state.phase == "lookup"
    assert state.next_retry_at == "2026-09-06T12:10:00Z"
    assert state.no_progress_runs == 0


def test_failed_run_without_persisted_transient_retry_is_blocked() -> None:
    """Block failures that lack durable transient error and retry evidence.

    Args:
        None.

    Returns:
        None.

    Examples:
        A failed persistence job leaves no changed manifest and cannot resume safely.
    """
    state = state_with_dispatch()
    blocked = catch_up.decide(
        state,
        Manifest(),
        now=NOW,
        workflow_run=catch_up.WorkflowRun(12, "completed", "failure"),
        manifest_sha256=DIGEST,
        controller_run_id="456",
    )
    assert blocked.action == "blocked"
    assert state.active is False


def test_no_progress_and_drained_unavailable_references_are_terminal() -> None:
    """Pause after repeated no-change batches and complete drained known gaps.

    Args:
        None.

    Returns:
        None.

    Examples:
        A 403 reference does not block completion once its queue is drained.
    """
    state = state_with_dispatch()
    state.no_progress_runs = 1
    blocked = catch_up.decide(
        state,
        Manifest(),
        now=NOW,
        workflow_run=catch_up.WorkflowRun(12, "completed", "success"),
        manifest_sha256=DIGEST,
        controller_run_id="456",
    )
    assert blocked.action == "blocked"
    assert "no durable progress" in state.last_error

    manifest = Manifest(discovery_errors={"https://palewi.re/unavailable/": "HTTP 403"})
    page = manifest.page("https://palewi.re/unavailable/")
    page.live_status = "error"
    state = catch_up.start(catch_up.CatchUpState())
    complete = catch_up.decide(
        state,
        manifest,
        now=NOW,
        workflow_run=None,
        manifest_sha256=DIGEST,
        controller_run_id="456",
    )
    assert complete.action == "complete"
    assert state.active is False


def test_catch_up_store_rejects_unknown_persisted_fields(tmp_path: Path) -> None:
    """Reject malformed durable state rather than replacing it.

    Args:
        tmp_path: Temporary test directory.

    Returns:
        None.

    Examples:
        An extra JSON field causes a clear state validation error.
    """
    path = tmp_path / "catch-up.json"
    value = catch_up._state_to_value(catch_up.CatchUpState())
    value["unexpected"] = True
    path.write_text(json.dumps(value))
    with pytest.raises(catch_up.CatchUpError, match="fields"):
        catch_up.CatchUpStore(path).load()
    assert "unexpected" in path.read_text()


def test_catch_up_store_round_trips_and_cli_controls(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Persist valid state and expose local start, status, stop, and tick commands.

    Args:
        tmp_path: Temporary test directory.
        monkeypatch: Replaces GitHub workflow lookup during the local tick.

    Returns:
        None.

    Examples:
        The CLI prints ``capture`` when a started state has a missing page.
    """
    state_path = tmp_path / "catch-up.json"
    manifest_path = tmp_path / "manifest.json"
    manifest = Manifest()
    live_page(manifest, "missing")
    ManifestStore(manifest_path).save(manifest)
    runner = CliRunner()

    assert runner.invoke(catch_up.cli, ["start", "--state", str(state_path)]).exit_code == 0
    assert catch_up.CatchUpStore(state_path).load().active is True
    status = runner.invoke(catch_up.cli, ["status", "--state", str(state_path)])
    assert status.exit_code == 0
    assert json.loads(status.output)["phase"] == "capture"
    monkeypatch.setattr(catch_up, "find_dispatched_run", lambda state: None)
    tick = runner.invoke(
        catch_up.cli,
        ["tick", "--manifest", str(manifest_path), "--state", str(state_path), "--controller-run-id", "123"],
    )
    assert tick.exit_code == 0
    assert tick.output.startswith("capture\n")
    assert runner.invoke(catch_up.cli, ["stop", "--state", str(state_path)]).exit_code == 0
    assert catch_up.CatchUpStore(state_path).load().phase == "complete"


def test_fetch_state_loads_optional_remote_state_at_manifest_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fetch controller JSON using the exact manifest branch-head token.

    Args:
        tmp_path: Temporary test directory.
        monkeypatch: Replaces GitHub branch and contents calls.

    Returns:
        None.

    Examples:
        A present remote state replaces the local controller state.
    """
    manifest_path = tmp_path / "manifest.json"
    state_path = tmp_path / "catch-up.json"
    token_path = tmp_path / "token.json"
    remote_state = catch_up.CatchUpState(active=True)

    def fake_fetch(path: Path, token: Path) -> None:
        """Write a valid manifest and matching branch token.

        Args:
            path: Local manifest destination.
            token: Local branch-token destination.

        Returns:
            None.

        Examples:
            The fake fetch prepares an immutable branch head.
        """
        ManifestStore(path).save(Manifest())
        token.write_text(
            json.dumps(
                {
                    "repository": DEFAULT_REPOSITORY,
                    "branch": DEFAULT_BRANCH,
                    "missing": False,
                    "head": "a" * 40,
                }
            )
        )

    class ContentClient:
        """Return the one serialized remote controller state."""

        def __init__(self, repository: str):
            """Validate the repository selection.

            Args:
                repository: Requested repository.

            Returns:
                None.

            Examples:
                The controller always uses the current repository.
            """
            assert repository == DEFAULT_REPOSITORY

        def content(self, head: str, path: str, *, required: bool) -> bytes:
            """Return state bytes at the requested immutable head.

            Args:
                head: Immutable data branch head.
                path: Requested data filename.
                required: Whether file absence is allowed.

            Returns:
                Serialized controller state.

            Examples:
                The optional catch-up state is available on the test branch.
            """
            assert head == "a" * 40
            assert path == catch_up.REMOTE_CATCH_UP_STATE
            assert required is False
            return (json.dumps(catch_up._state_to_value(remote_state)) + "\n").encode()

    monkeypatch.setattr("scripts.site_archive.branch.fetch", fake_fetch)
    monkeypatch.setattr(catch_up, "GitHubClient", ContentClient)
    catch_up.fetch_state(manifest_path, state_path, token_path)
    assert catch_up.CatchUpStore(state_path).load() == remote_state


def test_find_dispatched_run_matches_only_its_controller_label(monkeypatch: pytest.MonkeyPatch) -> None:
    """Find the labelled archive run without confusing ordinary manual runs.

    Args:
        monkeypatch: Replaces GitHub Actions response.

    Returns:
        None.

    Examples:
        Only the saved controller token identifies the in-flight batch.
    """
    state = state_with_dispatch()

    class RunClient:
        """Return ordinary and controller-labelled workflow runs."""

        def __init__(self, repository: str):
            """Validate the requested repository.

            Args:
                repository: Requested repository.

            Returns:
                None.

            Examples:
                Workflow status is read from the current repository.
            """
            assert repository == DEFAULT_REPOSITORY

        def request(self, endpoint: str) -> SimpleNamespace:
            """Return a workflow-run list.

            Args:
                endpoint: GitHub Actions endpoint.

            Returns:
                Response-shaped object containing workflow runs.

            Examples:
                The controller run appears after unrelated manual runs.
            """
            assert endpoint.endswith("event=workflow_dispatch&per_page=100")
            return SimpleNamespace(
                value={
                    "workflow_runs": [
                        {"id": 1, "status": "in_progress", "conclusion": None, "display_title": "Site archive"},
                        {
                            "id": 2,
                            "status": "queued",
                            "conclusion": None,
                            "display_title": "Site archive catch-up 123",
                        },
                    ]
                }
            )

    monkeypatch.setattr(catch_up, "GitHubClient", RunClient)
    assert catch_up.find_dispatched_run(state) == catch_up.WorkflowRun(2, "queued", None)


def test_push_state_rejects_stale_branch_before_any_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Refuse a controller-state write if another archive writer advanced the branch.

    Args:
        tmp_path: Temporary test directory.
        monkeypatch: Replaces GitHub client construction.

    Returns:
        None.

    Examples:
        A stale token raises instead of overwriting newer catch-up state.
    """
    state_path = tmp_path / "catch-up.json"
    token_path = tmp_path / "token.json"
    catch_up.CatchUpStore(state_path).save(catch_up.CatchUpState())
    token_path.write_text(
        json.dumps(
            {
                "repository": DEFAULT_REPOSITORY,
                "branch": DEFAULT_BRANCH,
                "missing": False,
                "head": "a" * 40,
            }
        )
    )

    class StaleClient:
        """Report a branch head that differs from the fetched token."""

        def __init__(self, repository: str):
            """Store the requested repository.

            Args:
                repository: Requested GitHub repository.

            Returns:
                None.

            Examples:
                ``StaleClient(DEFAULT_REPOSITORY)`` records the safe target.
            """
            assert repository == DEFAULT_REPOSITORY

        def ref(self, branch: str) -> str:
            """Return a newer protected data-branch head.

            Args:
                branch: Data branch name.

            Returns:
                Newer commit SHA.

            Examples:
                ``client.ref(DEFAULT_BRANCH)`` differs from the token head.
            """
            assert branch == DEFAULT_BRANCH
            return "b" * 40

    monkeypatch.setattr(catch_up, "GitHubClient", StaleClient)
    with pytest.raises(catch_up.CatchUpError, match="stale"):
        catch_up.push_state(state_path, token_path)


def test_push_state_writes_only_controller_file_with_a_fresh_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Write controller state without replacing the archive manifest tree entry.

    Args:
        tmp_path: Temporary test directory.
        monkeypatch: Replaces GitHub Git-database methods.

    Returns:
        None.

    Examples:
        A fresh data-branch token permits a non-forced state commit.
    """
    state_path = tmp_path / "catch-up.json"
    token_path = tmp_path / "token.json"
    catch_up.CatchUpStore(state_path).save(catch_up.CatchUpState(active=True))
    token_path.write_text(
        json.dumps(
            {
                "repository": DEFAULT_REPOSITORY,
                "branch": DEFAULT_BRANCH,
                "missing": False,
                "head": "a" * 40,
            }
        )
    )

    class FreshClient:
        """Provide a deterministic successful Git database update."""

        def __init__(self, repository: str):
            """Validate the requested repository.

            Args:
                repository: Requested repository.

            Returns:
                None.

            Examples:
                The state writer is scoped to the current repository.
            """
            assert repository == DEFAULT_REPOSITORY
            self.tree_path = ""

        def ref(self, branch: str) -> str:
            """Return the same branch head observed by fetch.

            Args:
                branch: Protected data branch.

            Returns:
                Current branch head.

            Examples:
                A matching head permits the controlled update.
            """
            assert branch == DEFAULT_BRANCH
            return "a" * 40

        def content(self, head: str, path: str, *, required: bool) -> bytes | None:
            """Report no prior controller-state file.

            Args:
                head: Immutable branch head.
                path: Requested file.
                required: Whether missing files are errors.

            Returns:
                None for the absent optional state.

            Examples:
                The first controller write creates only its state file.
            """
            assert head == "a" * 40
            assert path == catch_up.REMOTE_CATCH_UP_STATE
            assert required is False
            return None

        def create_blob(self, content: bytes) -> str:
            """Accept serialized state bytes.

            Args:
                content: Controller state content.

            Returns:
                New blob identifier.

            Examples:
                A valid JSON blob is added to the data tree.
            """
            assert b'"active": true' in content
            return "b" * 40

        def commit_tree(self, head: str) -> str:
            """Return the existing data tree.

            Args:
                head: Current branch head.

            Returns:
                Current tree identifier.

            Examples:
                Base-tree updates preserve the manifest.
            """
            assert head == "a" * 40
            return "c" * 40

        def create_tree(self, blob: str, tree: str, path: str) -> str:
            """Record the sole replacement path.

            Args:
                blob: New controller-state blob.
                tree: Existing base tree.
                path: Replaced data filename.

            Returns:
                New tree identifier.

            Examples:
                Only catch-up.json is replaced in the existing tree.
            """
            assert (blob, tree) == ("b" * 40, "c" * 40)
            assert path == catch_up.REMOTE_CATCH_UP_STATE
            return "d" * 40

        def create_commit(self, tree: str, parent: str) -> str:
            """Create a child state commit.

            Args:
                tree: New tree identifier.
                parent: Existing branch head.

            Returns:
                New commit identifier.

            Examples:
                A controller commit remains linear with archive commits.
            """
            assert (tree, parent) == ("d" * 40, "a" * 40)
            return "e" * 40

        def update_ref(self, branch: str, commit: str, *, create: bool) -> None:
            """Require a non-forced existing-ref update.

            Args:
                branch: Protected data branch.
                commit: New state commit.
                create: Whether a new branch would be created.

            Returns:
                None.

            Examples:
                Existing branch updates never create a replacement ref.
            """
            assert (branch, commit, create) == (DEFAULT_BRANCH, "e" * 40, False)

    monkeypatch.setattr(catch_up, "GitHubClient", FreshClient)
    catch_up.push_state(state_path, token_path)
    assert json.loads(token_path.read_text())["head"] == "e" * 40
