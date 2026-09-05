"""Checks for the archive workflow's cross-job checkpoint wiring."""

from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "site-archive.yaml"


def test_checkpoint_includes_hidden_files_and_restores_expected_directory() -> None:
    """Keep the persistent job's paths aligned with the uploaded artifact.

    Args:
        None.

    Returns:
        None.

    Examples:
        The hidden .site-archive directory must not be excluded by upload-artifact.
    """
    jobs = yaml.safe_load(WORKFLOW.read_text())["jobs"]
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
    jobs = yaml.safe_load(WORKFLOW.read_text())["jobs"]
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
    workflow = yaml.safe_load(WORKFLOW.read_text())
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
    steps = yaml.safe_load(WORKFLOW.read_text())["jobs"]["archive"]["steps"]
    failure = next(step for step in steps if step["name"] == "Surface synchronization failure")
    assert failure["if"] == "steps.sync.outcome == 'failure'"
    assert "exit 1" in failure["run"]
