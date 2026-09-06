"""Durably control GitHub Actions site-archive catch-up batches."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import click

from scripts.site_archive.branch import (
    DEFAULT_REPOSITORY,
    REMOTE_CATCH_UP_STATE,
    BranchPersistenceError,
    BranchToken,
    GitHubClient,
    _read_token,
    _write_token,
)
from scripts.site_archive.cli import is_due
from scripts.site_archive.manifest import ArchiveError, Manifest, ManifestStore, PageRecord
from scripts.site_archive.wayback import PENDING_COOLDOWN

STATE_FIELDS = {
    "active",
    "phase",
    "dispatch_token",
    "dispatched_at",
    "archive_run_id",
    "last_run_id",
    "next_retry_at",
    "last_error",
    "finished_at",
    "before_manifest_sha256",
    "before_archive_progress",
    "no_progress_runs",
}
PHASES = {"capture", "lookup", "blocked", "complete"}
WORKFLOW_NAME = "site-archive.yaml"
RUN_TITLE_PREFIX = "Site archive catch-up "
DISPATCH_GRACE = timedelta(minutes=15)
MAX_NO_PROGRESS_RUNS = 2


class CatchUpError(RuntimeError):
    """Raised when durable catch-up control state is invalid or unsafe."""


@dataclass
class CatchUpState:
    """Persisted controller state for the full-site archive catch-up."""

    active: bool = False
    phase: str = "capture"
    dispatch_token: str = ""
    dispatched_at: str = ""
    archive_run_id: int = 0
    last_run_id: int = 0
    next_retry_at: str = ""
    last_error: str = ""
    finished_at: str = ""
    before_manifest_sha256: str = ""
    before_archive_progress: int = 0
    no_progress_runs: int = 0


class CatchUpStore:
    """Validate and atomically save one local controller state file."""

    def __init__(self, path: Path):
        """Configure a store.

        Args:
            path: Local JSON state destination.

        Returns:
            None.

        Examples:
            ``CatchUpStore(Path(".site-archive/catch-up.json"))``.
        """
        self.path = path

    def load(self) -> CatchUpState:
        """Load controller state or return a safe inactive default when absent.

        Returns:
            Validated persisted state.

        Raises:
            CatchUpError: The existing JSON state is malformed.

        Examples:
            ``store.load().active`` reports whether catch-up is enabled.
        """
        if not self.path.exists() and not self.path.is_symlink():
            return CatchUpState()
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise CatchUpError(f"{self.path}: invalid catch-up state: {error}") from error
        return _state_from_value(value, str(self.path))

    def save(self, state: CatchUpState) -> None:
        """Validate and atomically save controller state.

        Args:
            state: Catch-up state to persist.

        Returns:
            None.

        Raises:
            CatchUpError: The state cannot be validated or saved.

        Examples:
            ``store.save(CatchUpState(active=True))`` enables a fresh catch-up.
        """
        value = _state_to_value(state)
        _state_from_value(value, str(self.path))
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        try:
            temporary.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            temporary.replace(self.path)
        except OSError as error:
            raise CatchUpError(f"{self.path}: unable to save catch-up state: {error}") from error


@dataclass(frozen=True)
class WorkflowRun:
    """The small subset of an archive Actions run used by the controller."""

    id: int
    status: str
    conclusion: str | None


@dataclass(frozen=True)
class ControllerDecision:
    """One action selected by an offline controller tick."""

    action: str
    detail: str


def _state_to_value(state: CatchUpState) -> dict[str, Any]:
    """Convert catch-up state to its one supported JSON form.

    Args:
        state: State instance to serialize.

    Returns:
        JSON-compatible state mapping.

    Raises:
        CatchUpError: The input is not a state instance.

    Examples:
        ``_state_to_value(CatchUpState())["active"]`` is False.
    """
    if not isinstance(state, CatchUpState):
        raise CatchUpError("catch-up state must be a CatchUpState")
    return asdict(state)


def _state_from_value(value: Any, location: str) -> CatchUpState:
    """Validate and reconstruct catch-up state from decoded JSON.

    Args:
        value: Decoded JSON value.
        location: Human-readable source identifier.

    Returns:
        Validated catch-up state.

    Raises:
        CatchUpError: The JSON has unsupported or contradictory values.

    Examples:
        ``_state_from_value(_state_to_value(CatchUpState()), "state")`` succeeds.
    """
    if not isinstance(value, dict) or set(value) != STATE_FIELDS:
        raise CatchUpError(f"{location}: invalid catch-up state fields")
    if type(value["active"]) is not bool:
        raise CatchUpError(f"{location}: active must be a boolean")
    if not isinstance(value["phase"], str) or value["phase"] not in PHASES:
        raise CatchUpError(f"{location}: invalid phase")
    for name in (
        "dispatch_token",
        "dispatched_at",
        "next_retry_at",
        "last_error",
        "finished_at",
        "before_manifest_sha256",
    ):
        if not isinstance(value[name], str):
            raise CatchUpError(f"{location}: {name} must be a string")
    for name in ("dispatched_at", "next_retry_at", "finished_at"):
        _timestamp(value[name], f"{location}: {name}")
    if value["dispatch_token"] and not value["dispatch_token"].isdigit():
        raise CatchUpError(f"{location}: dispatch_token must be a GitHub run ID")
    if type(value["archive_run_id"]) is not int or value["archive_run_id"] < 0:
        raise CatchUpError(f"{location}: archive_run_id must be a non-negative integer")
    if type(value["last_run_id"]) is not int or value["last_run_id"] < 0:
        raise CatchUpError(f"{location}: last_run_id must be a non-negative integer")
    if type(value["no_progress_runs"]) is not int or value["no_progress_runs"] < 0:
        raise CatchUpError(f"{location}: no_progress_runs must be a non-negative integer")
    if type(value["before_archive_progress"]) is not int or value["before_archive_progress"] < 0:
        raise CatchUpError(f"{location}: before_archive_progress must be a non-negative integer")
    digest = value["before_manifest_sha256"]
    if digest and (len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest)):
        raise CatchUpError(f"{location}: before_manifest_sha256 must be a lowercase SHA-256")
    dispatched = bool(value["dispatch_token"])
    if dispatched != bool(value["dispatched_at"]) or dispatched != bool(value["before_manifest_sha256"]):
        raise CatchUpError(f"{location}: dispatch fields must be present together")
    if not dispatched and value["archive_run_id"]:
        raise CatchUpError(f"{location}: archive_run_id requires a dispatched run")
    if value["phase"] in {"blocked", "complete"} and value["active"]:
        raise CatchUpError(f"{location}: terminal phases cannot remain active")
    return CatchUpState(**value)


def _timestamp(value: str, location: str) -> None:
    """Validate one optional UTC ISO timestamp.

    Args:
        value: Empty or UTC timestamp string.
        location: Human-readable state-field location.

    Returns:
        None.

    Raises:
        CatchUpError: The timestamp is not valid UTC ISO text.

    Examples:
        ``_timestamp("2026-09-06T12:00:00Z", "state")`` succeeds.
    """
    if not value:
        return
    if not value.endswith(("Z", "+00:00")):
        raise CatchUpError(f"{location}: must be a UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise CatchUpError(f"{location}: invalid timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise CatchUpError(f"{location}: must be a UTC timestamp")


def start(state: CatchUpState) -> CatchUpState:
    """Enable catch-up starting with known missing archive pages.

    Args:
        state: Existing controller state.

    Returns:
        Reset active state ready for a capture batch.

    Examples:
        ``start(CatchUpState()).phase`` is ``"capture"``.
    """
    state.active = True
    state.phase = "capture"
    state.dispatch_token = ""
    state.dispatched_at = ""
    state.archive_run_id = 0
    state.next_retry_at = ""
    state.last_error = ""
    state.finished_at = ""
    state.before_manifest_sha256 = ""
    state.before_archive_progress = 0
    state.no_progress_runs = 0
    return state


def stop(state: CatchUpState, now: datetime) -> CatchUpState:
    """Disable catch-up without changing archive inventory evidence.

    Args:
        state: Existing controller state.
        now: Current timezone-aware UTC time.

    Returns:
        Inactive state marked complete by an explicit operator stop.

    Examples:
        ``stop(CatchUpState(active=True), now).active`` is False.
    """
    state.active = False
    state.phase = "complete"
    state.dispatch_token = ""
    state.dispatched_at = ""
    state.archive_run_id = 0
    state.next_retry_at = ""
    state.finished_at = _utc_text(now)
    state.before_manifest_sha256 = ""
    state.before_archive_progress = 0
    return state


def decide(
    state: CatchUpState,
    manifest: Manifest,
    *,
    now: datetime,
    workflow_run: WorkflowRun | None,
    manifest_sha256: str,
    controller_run_id: str,
) -> ControllerDecision:
    """Advance state and select at most one safe action for a controller run.

    Args:
        state: Mutable durable controller state.
        manifest: Fresh archive manifest from the data branch.
        now: Current timezone-aware UTC time.
        workflow_run: Matching dispatched archive run, when known.
        manifest_sha256: Exact digest of the freshly fetched manifest.
        controller_run_id: Current controller Actions run ID used to label a dispatch.

    Returns:
        Selected action: ``capture``, ``lookup``, ``wait``, ``idle``, ``blocked``, or ``complete``.

    Raises:
        CatchUpError: Required controller inputs are invalid.

    Examples:
        ``decide(state, manifest, now=now, workflow_run=None, manifest_sha256=digest, controller_run_id="1")``.
    """
    _require_utc(now)
    if not controller_run_id.isdigit():
        raise CatchUpError("controller_run_id must be a GitHub run ID")
    if len(manifest_sha256) != 64:
        raise CatchUpError("manifest_sha256 must be a SHA-256")
    if not state.active:
        return ControllerDecision("idle", "Catch-up is not active.")
    if state.dispatch_token:
        settled = _settle_dispatched_run(state, manifest, now, workflow_run, manifest_sha256)
        if settled is not None:
            return settled
    retry_at = _parse_timestamp(state.next_retry_at)
    if retry_at and now < retry_at:
        return ControllerDecision("wait", f"Waiting until {state.next_retry_at}.")
    action, detail, retry = _next_action(state.phase, manifest, now)
    if action in {"capture", "lookup"}:
        state.dispatch_token = controller_run_id
        state.dispatched_at = _utc_text(now)
        state.before_manifest_sha256 = manifest_sha256
        state.before_archive_progress = archive_progress(manifest)
        state.next_retry_at = _utc_text(now + DISPATCH_GRACE)
        state.last_error = ""
        state.finished_at = ""
        state.phase = "lookup" if action == "capture" else "capture"
        return ControllerDecision(action, detail)
    if action == "wait":
        assert retry is not None
        state.next_retry_at = _utc_text(retry)
        return ControllerDecision("wait", detail)
    state.active = False
    state.phase = action
    state.finished_at = _utc_text(now)
    state.next_retry_at = ""
    return ControllerDecision(action, detail)


def _settle_dispatched_run(
    state: CatchUpState,
    manifest: Manifest,
    now: datetime,
    workflow_run: WorkflowRun | None,
    manifest_sha256: str,
) -> ControllerDecision | None:
    """Wait for or record the result of the only archive run in flight.

    Args:
        state: Mutable state with a dispatch token.
        manifest: Fresh archive manifest after the dispatched batch.
        now: Current UTC time.
        workflow_run: Matching archive Actions run, if visible.
        manifest_sha256: Current manifest digest.

    Returns:
        Safe wait or blocked action, or None when the completed batch allows
        immediate next-phase selection.

    Examples:
        A queued run returns ``ControllerDecision("wait", ...)``.
    """
    dispatched_at = _parse_timestamp(state.dispatched_at)
    assert dispatched_at is not None
    if workflow_run is None:
        if now < dispatched_at + DISPATCH_GRACE:
            return ControllerDecision("wait", "Waiting for the dispatched archive run to appear.")
        return _block(state, now, "The dispatched archive run did not appear within 15 minutes.")
    state.archive_run_id = workflow_run.id
    if workflow_run.status != "completed":
        return ControllerDecision("wait", f"Archive run {workflow_run.id} is {workflow_run.status}.")
    state.last_run_id = workflow_run.id
    state.archive_run_id = 0
    state.dispatch_token = ""
    state.dispatched_at = ""
    state.next_retry_at = ""
    made_archive_progress = archive_progress(manifest) > state.before_archive_progress
    manifest_changed = state.before_manifest_sha256 != manifest_sha256
    if workflow_run.conclusion != "success":
        retry_at = _transient_retry(manifest, now) if manifest_changed else None
        state.before_manifest_sha256 = ""
        state.before_archive_progress = 0
        if retry_at is not None:
            state.phase = "lookup"
            state.next_retry_at = _utc_text(max(retry_at, now + timedelta(minutes=10)))
            if made_archive_progress:
                state.no_progress_runs = 0
            return ControllerDecision(
                "wait",
                f"Archive run {workflow_run.id} made partial progress and will retry after {state.next_retry_at}.",
            )
        return _block(
            state,
            now,
            f"Archive run {workflow_run.id} ended with {workflow_run.conclusion or 'no conclusion'}.",
        )
    if state.before_manifest_sha256 == manifest_sha256:
        state.no_progress_runs += 1
    else:
        state.no_progress_runs = 0
    state.before_manifest_sha256 = ""
    state.before_archive_progress = 0
    if state.no_progress_runs >= MAX_NO_PROGRESS_RUNS:
        return _block(state, now, "Two successful archive batches made no durable progress.")
    return None


def _next_action(phase: str, manifest: Manifest, now: datetime) -> tuple[str, str, datetime | None]:
    """Choose the next work phase from persisted inventory evidence.

    Args:
        phase: Preferred phase after the last completed batch.
        manifest: Fresh archive inventory.
        now: Current UTC time.

    Returns:
        Action name, explanation, and optional retry time.

    Examples:
        A due missing page selects ``"capture"`` during the capture phase.
    """
    missing = _due_missing(manifest)
    lookup_needed = _lookup_needed(manifest, now)
    if phase == "capture" and missing:
        return "capture", f"Requesting captures for {len(missing)} known missing live pages.", None
    if phase == "lookup" and lookup_needed:
        return "lookup", "Checking pending, unknown, and discovery work.", None
    if missing:
        return "capture", f"Requesting captures for {len(missing)} known missing live pages.", None
    if lookup_needed:
        return "lookup", "Checking pending, unknown, and discovery work.", None
    retry_at = _next_retry(manifest, now)
    if retry_at:
        return "wait", f"Waiting for the next permitted archive check at {_utc_text(retry_at)}.", retry_at
    return (
        "complete",
        "All known live pages are archived or blocked; discovery is drained and unavailable references remain recorded.",
        None,
    )


def archive_progress(manifest: Manifest) -> int:
    """Count confirmed archives and unambiguous successful capture candidates.

    Args:
        manifest: Archive inventory to inspect.

    Returns:
        Count of confirmed snapshots plus pending captures with a returned URL.

    Examples:
        ``archive_progress(Manifest())`` is zero.
    """
    return sum(
        page.archive_status == "archived" or (page.archive_status == "pending" and bool(page.pending_archive_url))
        for page in manifest.pages.values()
    )


def _transient_retry(manifest: Manifest, now: datetime) -> datetime | None:
    """Find a current Wayback retry deadline from persisted transient failures.

    Args:
        manifest: Fresh archive inventory after a failed batch.
        now: Current UTC time.

    Returns:
        Earliest eligible retry time, or None for configuration or validation failures.

    Examples:
        A rate-limited Wayback request returns its recorded retry time.
    """
    retries: list[datetime] = []
    for page in manifest.pages.values():
        retry_at = _parse_timestamp(page.next_retry_at)
        if (
            page.last_check_status == "error"
            and retry_at is not None
            and page.last_error.startswith("Wayback ")
            and "SAVEPAGENOW_" not in page.last_error
        ):
            retries.append(retry_at)
    return min(retries, default=None)


def _due_missing(manifest: Manifest) -> list[PageRecord]:
    """Return live, missing archive records that can be submitted now.

    Args:
        manifest: Archive inventory to inspect.

    Returns:
        Due missing live pages.

    Examples:
        ``_due_missing(Manifest())`` is an empty list.
    """
    return [
        page
        for page in manifest.pages.values()
        if page.live_status == "live" and page.archive_status == "missing" and is_due(page)
    ]


def _lookup_needed(manifest: Manifest, now: datetime) -> bool:
    """Determine whether a lookup/discovery batch can make safe progress now.

    Args:
        manifest: Archive inventory to inspect.
        now: Current UTC time.

    Returns:
        Whether lookup-only synchronization is due.

    Examples:
        A nonempty discovery queue requires a lookup batch.
    """
    if manifest.discovery_queue:
        return True
    for page in manifest.pages.values():
        if page.live_status != "live" or not is_due(page):
            continue
        if page.archive_status == "unknown":
            return True
        if page.archive_status == "pending" and _pending_due(page, now):
            return True
    return False


def _next_retry(manifest: Manifest, now: datetime) -> datetime | None:
    """Find the earliest retry deadline for remaining but currently deferred work.

    Args:
        manifest: Archive inventory to inspect.
        now: Current UTC time.

    Returns:
        Earliest future permitted time, or None when no deferred work exists.

    Examples:
        ``_next_retry(Manifest(), now)`` returns None.
    """
    retries: list[datetime] = []
    for page in manifest.pages.values():
        if page.live_status != "live":
            continue
        retry = _parse_timestamp(page.next_retry_at)
        if retry and retry > now and page.archive_status in {"unknown", "missing", "pending"}:
            retries.append(retry)
        if page.archive_status == "pending":
            submitted = _parse_timestamp(page.last_submit_at)
            if submitted:
                due = submitted + PENDING_COOLDOWN
                if due > now:
                    retries.append(due)
    return min(retries, default=None)


def _pending_due(page: PageRecord, now: datetime) -> bool:
    """Determine whether a pending submission has passed its 24-hour wait.

    Args:
        page: Pending archive record.
        now: Current UTC time.

    Returns:
        Whether independent confirmation may be requested now.

    Examples:
        A freshly submitted page returns False.
    """
    submitted = _parse_timestamp(page.last_submit_at)
    return submitted is not None and now >= submitted + PENDING_COOLDOWN


def _parse_timestamp(value: str) -> datetime | None:
    """Parse an optional validated UTC timestamp.

    Args:
        value: Empty or ISO UTC timestamp.

    Returns:
        Parsed UTC time or None.

    Examples:
        ``_parse_timestamp("")`` returns None.
    """
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _utc_text(value: datetime) -> str:
    """Serialize a timezone-aware time using the persistent UTC form.

    Args:
        value: Time to serialize.

    Returns:
        ISO UTC timestamp ending in ``Z``.

    Examples:
        ``_utc_text(now).endswith("Z")`` is True.
    """
    _require_utc(value)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _require_utc(value: datetime) -> None:
    """Require a timezone-aware UTC-compatible time.

    Args:
        value: Time to validate.

    Returns:
        None.

    Raises:
        CatchUpError: The value has no timezone.

    Examples:
        ``_require_utc(datetime.now(UTC))`` succeeds.
    """
    if value.tzinfo is None:
        raise CatchUpError("time must be timezone-aware")


def _block(state: CatchUpState, now: datetime, detail: str) -> ControllerDecision:
    """Record a terminal pause that requires an explicit manual resume.

    Args:
        state: Mutable controller state.
        now: Current UTC time.
        detail: Clear operator-facing pause reason.

    Returns:
        Blocked decision.

    Examples:
        ``_block(state, now, "Archive run failed").action`` is ``"blocked"``.
    """
    state.active = False
    state.phase = "blocked"
    state.last_error = detail
    state.next_retry_at = ""
    state.finished_at = _utc_text(now)
    state.before_manifest_sha256 = ""
    state.before_archive_progress = 0
    return ControllerDecision("blocked", detail)


def manifest_digest(path: Path) -> str:
    """Return the exact SHA-256 digest for a fetched manifest file.

    Args:
        path: Validated local manifest file.

    Returns:
        Lowercase SHA-256 text.

    Raises:
        CatchUpError: The file cannot be read.

    Examples:
        ``len(manifest_digest(Path("manifest.json")))`` is 64.
    """
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise CatchUpError(f"{path}: unable to read manifest: {error}") from error


def fetch_state(manifest_path: Path, state_path: Path, state_token: Path) -> None:
    """Fetch the manifest and optional controller state at the same branch head.

    Args:
        manifest_path: Local archive manifest destination.
        state_path: Local controller state destination.
        state_token: Optimistic branch-head token destination.

    Returns:
        None.

    Raises:
        CatchUpError: The data branch or local state is unsafe.

    Examples:
        ``fetch_state(manifest, state, token)`` prepares one controller run.
    """
    from scripts.site_archive.branch import fetch

    try:
        fetch(manifest_path, state_token)
        token = _read_token(state_token)
        if token.head is None:
            raise CatchUpError("site-archive-data does not yet contain an archive manifest")
        content = GitHubClient(token.repository).content(token.head, REMOTE_CATCH_UP_STATE, required=False)
        if content is None:
            CatchUpStore(state_path).save(CatchUpState())
            return
        temporary = state_path.with_suffix(f"{state_path.suffix}.fetch.tmp")
        temporary.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_bytes(content)
        CatchUpStore(temporary).load()
        temporary.replace(state_path)
    except (ArchiveError, BranchPersistenceError, OSError) as error:
        raise CatchUpError(str(error)) from error


def push_state(state_path: Path, state_token: Path) -> None:
    """Persist controller state with the fetched data-branch head as a lock.

    Args:
        state_path: Validated local controller state.
        state_token: Token written by :func:`fetch_state`.

    Returns:
        None.

    Raises:
        CatchUpError: The branch changed or state cannot be safely written.

    Examples:
        ``push_state(state, token)`` saves a controller transition.
    """
    try:
        CatchUpStore(state_path).load()
        content = state_path.read_bytes()
        token = _read_token(state_token)
        if token.head is None:
            raise CatchUpError("cannot create catch-up state before the archive manifest exists")
        client = GitHubClient(token.repository)
        if client.ref(token.branch) != token.head:
            raise CatchUpError("branch changed since fetch; refusing stale catch-up write")
        remote = client.content(token.head, REMOTE_CATCH_UP_STATE, required=False)
        if remote == content:
            click.echo("Catch-up state is unchanged; no commit created.")
            return
        tree = client.create_tree(
            client.create_blob(content),
            client.commit_tree(token.head),
            REMOTE_CATCH_UP_STATE,
        )
        commit = client.create_commit(tree, token.head)
        client.update_ref(token.branch, commit, create=False)
        _write_token(state_token, BranchToken(token.repository, token.branch, commit))
        click.echo(f"Persisted {REMOTE_CATCH_UP_STATE} at {commit}.")
    except (ArchiveError, BranchPersistenceError, OSError) as error:
        raise CatchUpError(str(error)) from error


def find_dispatched_run(state: CatchUpState) -> WorkflowRun | None:
    """Find the one archive Actions run labelled by the saved controller token.

    Args:
        state: Controller state with a nonempty dispatch token.

    Returns:
        Matching archive workflow run, or None when it is not visible yet.

    Raises:
        CatchUpError: GitHub returns malformed workflow data.

    Examples:
        ``find_dispatched_run(state)`` checks the current archive batch.
    """
    if not state.dispatch_token:
        return None
    try:
        value = (
            GitHubClient(DEFAULT_REPOSITORY)
            .request(f"actions/workflows/{WORKFLOW_NAME}/runs?event=workflow_dispatch&per_page=100")
            .value
        )
    except BranchPersistenceError as error:
        raise CatchUpError(f"cannot read archive workflow runs: {error}") from error
    if not isinstance(value, dict) or not isinstance(value.get("workflow_runs"), list):
        raise CatchUpError("GitHub returned malformed archive workflow runs")
    expected = f"{RUN_TITLE_PREFIX}{state.dispatch_token}"
    for run in value["workflow_runs"]:
        if not isinstance(run, dict) or run.get("display_title") != expected:
            continue
        run_id = run.get("id")
        status = run.get("status")
        conclusion = run.get("conclusion")
        if (
            type(run_id) is not int
            or not isinstance(status, str)
            or conclusion is not None
            and not isinstance(conclusion, str)
        ):
            raise CatchUpError("GitHub returned malformed archive workflow run")
        return WorkflowRun(run_id, status, conclusion)
    return None


@click.group()
def cli() -> None:
    """Manage durable GitHub Actions catch-up state.

    Returns:
        None.

    Examples:
        ``uv run python -m scripts.site_archive.catch_up status`` reports state.
    """


@cli.command("fetch")
@click.option("--manifest", "manifest_path", type=click.Path(path_type=Path), required=True)
@click.option("--state", "state_path", type=click.Path(path_type=Path), required=True)
@click.option("--state-token", type=click.Path(path_type=Path), required=True)
def fetch_command(manifest_path: Path, state_path: Path, state_token: Path) -> None:
    """Fetch archive and controller state from the protected data branch.

    Args:
        manifest_path: Local archive manifest destination.
        state_path: Local controller state destination.
        state_token: Local branch-head token destination.

    Returns:
        None.

    Examples:
        ``... catch_up fetch --manifest manifest.json --state catch-up.json --state-token token.json``.
    """
    try:
        fetch_state(manifest_path, state_path, state_token)
    except CatchUpError as error:
        raise click.ClickException(str(error)) from error


@cli.command("push")
@click.option("--state", "state_path", type=click.Path(path_type=Path), required=True)
@click.option("--state-token", type=click.Path(path_type=Path), required=True)
def push_command(state_path: Path, state_token: Path) -> None:
    """Persist controller state to the protected data branch.

    Args:
        state_path: Local controller state file.
        state_token: Local branch-head token produced by fetch.

    Returns:
        None.

    Examples:
        ``... catch_up push --state catch-up.json --state-token token.json``.
    """
    try:
        push_state(state_path, state_token)
    except CatchUpError as error:
        raise click.ClickException(str(error)) from error


@cli.command("start")
@click.option("--state", "state_path", type=click.Path(path_type=Path), required=True)
def start_command(state_path: Path) -> None:
    """Enable catch-up after a controller-state fetch.

    Args:
        state_path: Local controller state path.

    Returns:
        None.

    Examples:
        ``... catch_up start --state catch-up.json`` enables capture work.
    """
    store = CatchUpStore(state_path)
    store.save(start(store.load()))


@cli.command("stop")
@click.option("--state", "state_path", type=click.Path(path_type=Path), required=True)
def stop_command(state_path: Path) -> None:
    """Disable catch-up after a controller-state fetch.

    Args:
        state_path: Local controller state path.

    Returns:
        None.

    Examples:
        ``... catch_up stop --state catch-up.json`` stops later dispatches.
    """
    store = CatchUpStore(state_path)
    store.save(stop(store.load(), datetime.now(UTC)))


@cli.command("status")
@click.option("--state", "state_path", type=click.Path(path_type=Path), required=True)
def status_command(state_path: Path) -> None:
    """Print validated controller state as JSON.

    Args:
        state_path: Local controller state path.

    Returns:
        None.

    Examples:
        ``... catch_up status --state catch-up.json`` prints durable status.
    """
    click.echo(json.dumps(_state_to_value(CatchUpStore(state_path).load()), indent=2, sort_keys=True))


@cli.command("tick")
@click.option("--manifest", "manifest_path", type=click.Path(path_type=Path), required=True)
@click.option("--state", "state_path", type=click.Path(path_type=Path), required=True)
@click.option("--controller-run-id", required=True)
def tick_command(manifest_path: Path, state_path: Path, controller_run_id: str) -> None:
    """Select and save one controller action using fetched durable data.

    Args:
        manifest_path: Fresh local archive manifest.
        state_path: Fresh local controller state.
        controller_run_id: Current controller Actions run ID.

    Returns:
        None.

    Examples:
        ``... catch_up tick --manifest manifest.json --state catch-up.json --controller-run-id 1``.
    """
    try:
        store = CatchUpStore(state_path)
        state = store.load()
        decision = decide(
            state,
            ManifestStore(manifest_path).load(),
            now=datetime.now(UTC),
            workflow_run=find_dispatched_run(state),
            manifest_sha256=manifest_digest(manifest_path),
            controller_run_id=controller_run_id,
        )
        store.save(state)
        click.echo(decision.action)
        click.echo(decision.detail, err=True)
    except (ArchiveError, CatchUpError, OSError) as error:
        raise click.ClickException(str(error)) from error


if __name__ == "__main__":
    cli()
