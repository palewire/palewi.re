"""Checks for the archive workflow's cross-job checkpoint wiring."""

from pathlib import Path
from typing import Any

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "site-archive.yaml"


def load_workflow() -> dict[Any, Any]:
    """Load the archive workflow while preserving PyYAML's legacy `on` key.

    Args:
        None.

    Returns:
        Parsed GitHub Actions workflow.

    Examples:
        ``load_workflow()["jobs"]`` returns the configured jobs.
    """
    return yaml.safe_load(WORKFLOW.read_text())


def archive_step() -> dict[str, Any]:
    """Return the workflow step that performs archive maintenance.

    Args:
        None.

    Returns:
        Parsed synchronization step.

    Examples:
        ``archive_step()["id"]`` is ``"sync"``.
    """
    workflow = load_workflow()
    jobs = workflow["jobs"]
    return next(step for step in jobs["archive"]["steps"] if step.get("id") == "sync")


def test_checkpoint_includes_hidden_files_and_restores_expected_directory() -> None:
    """Keep the persistent job's paths aligned with the uploaded artifact.

    Args:
        None.

    Returns:
        None.

    Examples:
        The hidden .site-archive directory must not be excluded by upload-artifact.
    """
    jobs = load_workflow()["jobs"]
    upload = next(step for step in jobs["archive"]["steps"] if step.get("uses", "").startswith("actions/upload-"))
    download = next(step for step in jobs["persist"]["steps"] if step.get("uses", "").startswith("actions/download-"))
    assert upload["with"]["include-hidden-files"] is True
    assert upload["with"]["if-no-files-found"] == "error"
    assert upload["with"]["name"] == download["with"]["name"]
    assert download["with"]["path"] == ".site-archive"
    assert ".site-archive/manifest.json" in upload["with"]["path"]
    assert ".site-archive/state-token.json" in upload["with"]["path"]
    assert "always()" in upload["if"]
    assert "always()" in jobs["persist"]["if"]


def test_artifact_actions_are_pinned_to_node24_releases() -> None:
    """Use current artifact actions that run on the supported Node version.

    Args:
        None.

    Returns:
        None.

    Examples:
        The upload and download steps use the verified v7 and v8 release commits.
    """
    jobs = load_workflow()["jobs"]
    upload = next(step for step in jobs["archive"]["steps"] if step.get("uses", "").startswith("actions/upload-"))
    download = next(step for step in jobs["persist"]["steps"] if step.get("uses", "").startswith("actions/download-"))
    assert upload["uses"] == "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
    assert download["uses"] == "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c"


def test_only_persistence_can_write_and_both_jobs_use_the_same_source() -> None:
    """Limit write access and prevent different code between archive and persist.

    Args:
        None.

    Returns:
        None.

    Examples:
        A push to main during a long run cannot change its persistence code.
    """
    workflow = load_workflow()
    jobs = workflow["jobs"]
    assert jobs["archive"]["permissions"]["contents"] == "read"
    assert jobs["persist"]["permissions"]["contents"] == "write"
    assert workflow["concurrency"]["cancel-in-progress"] is False
    for job in jobs.values():
        checkout = next(step for step in job["steps"] if step.get("uses", "").startswith("actions/checkout@"))
        assert checkout["with"]["ref"] == "${{ github.sha }}"
        assert checkout["with"]["persist-credentials"] is False
    assert "SAVEPAGENOW_SECRET_KEY" not in jobs["persist"]["env"]


def test_lookup_failures_are_not_hidden_by_checkpoint_recovery() -> None:
    """Report synchronization failures after recovery files have been uploaded.

    Args:
        None.

    Returns:
        None.

    Examples:
        Saving partial progress must not turn a failed archive run green.
    """
    steps = load_workflow()["jobs"]["archive"]["steps"]
    failure = next(step for step in steps if step["name"] == "Surface synchronization failure")
    assert failure["if"] == "steps.sync.outcome == 'failure'"
    assert "exit 1" in failure["run"]


def test_scheduled_runs_keep_the_existing_sync_limits() -> None:
    """Keep the default weekly run scoped to its established batch sizes.

    Args:
        None.

    Returns:
        None.

    Examples:
        A schedule run selects sync with 100 discoveries, checks, and a 10-page capture limit.
    """
    workflow = load_workflow()
    dispatch = workflow[True]["workflow_dispatch"]
    inputs = dispatch["inputs"]
    run = archive_step()["run"]

    assert workflow[True]["schedule"] == [{"cron": "17 6 * * 1"}]
    assert inputs["lookup_only"]["default"] is False
    assert inputs["capture_only"]["default"] is False
    assert inputs["max_captures"]["default"] == 10
    assert "MAX_CAPTURES: ${{ inputs.max_captures || '10' }}" in WORKFLOW.read_text()
    assert "--max-pages 100" in run
    assert "--max-checks 100" in run
    assert '--max-captures "$MAX_CAPTURES"' in run
    assert "sync" in run


def test_capture_only_selects_capture_command_without_discovery_or_lookup() -> None:
    """Keep manual capture-only runs separate from the full synchronization path.

    Args:
        None.

    Returns:
        None.

    Examples:
        A 62-page manual batch calls ``capture`` with the configured limit.
    """
    run = archive_step()["run"]
    capture_branch, sync_branch = run.split("fi\nargs=(", maxsplit=1)

    assert 'if test "$CAPTURE_ONLY" = "true"; then' in capture_branch
    assert "scripts.site_archive capture" in capture_branch
    assert '--manifest "$MANIFEST"' in capture_branch
    assert '--max-captures "$MAX_CAPTURES"' in capture_branch
    assert "--max-seconds 900" in capture_branch
    assert '--summary "$SUMMARY"' in capture_branch
    assert "scripts.site_archive sync" not in capture_branch
    assert "sync\n" in sync_branch


def test_manual_inputs_reject_conflicting_flags_and_unsafe_capture_limits() -> None:
    """Require one unambiguous mode and a bounded whole-number capture limit.

    Args:
        None.

    Returns:
        None.

    Examples:
        ``lookup_only`` and ``capture_only`` cannot both be true.
    """
    run = archive_step()["run"]

    assert 'if test "$LOOKUP_ONLY" = "true" && test "$CAPTURE_ONLY" = "true"; then' in run
    assert "lookup_only and capture_only cannot both be enabled." in run
    assert '[[ "$MAX_CAPTURES" =~ ^[1-9][0-9]*$ ]]' in run
    assert 'test "$MAX_CAPTURES" -gt 100' in run
    assert "max_captures must be a whole number from 1 through 100." in run
    assert archive_step()["continue-on-error"] is True
