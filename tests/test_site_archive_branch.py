"""Tests for safe site archive branch persistence."""

from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from scripts.site_archive.branch import (
    DEFAULT_BRANCH,
    DEFAULT_REPOSITORY,
    BranchPersistenceError,
    cli,
    fetch,
    push,
)
from scripts.site_archive.manifest import Manifest, ManifestStore

HEAD = "a" * 40
TREE = "b" * 40
BLOB = "c" * 40
COMMIT = "d" * 40


def manifest_bytes(tmp_path: Path) -> tuple[Path, bytes]:
    """Create one valid manifest fixture.

    Args:
        tmp_path: Test directory.

    Returns:
        Manifest path and its exact persisted bytes.

    Examples:
        ``manifest_bytes(tmp_path)`` supplies a publishable state file.
    """
    path = tmp_path / "manifest.json"
    ManifestStore(path).save(Manifest())
    return path, path.read_bytes()


class GhStub:
    """Return deterministic responses for the GitHub REST calls."""

    def __init__(self, *, head: str | None = HEAD, remote: bytes | None = None) -> None:
        """Initialize a deterministic GitHub API fixture.

        Args:
            head: Current branch head, or ``None`` for an absent branch.
            remote: Existing manifest bytes returned by the contents endpoint.

        Returns:
            None.

        Examples:
            ``GhStub(head=None)`` models a first persistence run.
        """
        self.head = head
        self.remote = remote
        self.calls: list[tuple[list[str], str | None]] = []

    def __call__(self, command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        """Handle one ``gh api`` subprocess invocation.

        Args:
            command: Command arguments.
            kwargs: Subprocess keyword arguments.

        Returns:
            A mocked completed process.

        Examples:
            ``stub(command, input=...)`` records JSON sent over stdin.
        """
        self.calls.append((command, kwargs.get("input")))
        endpoint = command[2]
        method = command[command.index("--method") + 1]
        if endpoint in {"repos/palewire/palewi.re", "repos/palewire/palewi.re/"}:
            return self.ok({})
        if endpoint.endswith("/git/ref/heads/site-archive-data"):
            if self.head is None:
                return self.fail("gh: Not Found (HTTP 404)")
            return self.ok({"object": {"sha": self.head}})
        if endpoint.startswith("repos/palewire/palewi.re/contents/manifest.json"):
            assert self.remote is not None
            return self.ok(
                {
                    "encoding": "base64",
                    "content": base64.b64encode(self.remote).decode(),
                }
            )
        if endpoint.endswith(f"/git/commits/{HEAD}"):
            return self.ok({"tree": {"sha": TREE}})
        if endpoint.endswith("/git/blobs"):
            return self.ok({"sha": BLOB})
        if endpoint.endswith("/git/trees"):
            return self.ok({"sha": TREE})
        if endpoint.endswith("/git/commits"):
            return self.ok({"sha": COMMIT})
        if endpoint.endswith("/git/refs"):
            assert method == "POST"
            self.head = COMMIT
            return self.ok({"ref": "refs/heads/site-archive-data"})
        if endpoint.endswith("/git/refs/heads/site-archive-data"):
            assert method == "PATCH"
            payload = json.loads(self.calls[-1][1] or "{}")
            assert payload["force"] is False
            self.head = COMMIT
            return self.ok({"object": {"sha": COMMIT}})
        raise AssertionError(f"unexpected endpoint {endpoint}")

    @staticmethod
    def ok(value: object) -> subprocess.CompletedProcess[str]:
        """Build a successful subprocess result.

        Args:
            value: JSON response.

        Returns:
            Completed process fixture.

        Examples:
            ``GhStub.ok({"sha": "..."})`` models a GitHub response.
        """
        return subprocess.CompletedProcess(["gh"], 0, json.dumps(value), "")

    @staticmethod
    def fail(stderr: str) -> subprocess.CompletedProcess[str]:
        """Build a failed subprocess result.

        Args:
            stderr: Sanitized API error.

        Returns:
            Failed process fixture.

        Examples:
            ``GhStub.fail("HTTP 403")`` models a permission failure.
        """
        return subprocess.CompletedProcess(["gh"], 1, "", stderr)


def token(path: Path, head: str | None = HEAD) -> None:
    """Write a valid state token fixture.

    Args:
        path: Token destination.
        head: Observed branch head, or ``None`` for absent branch.

    Returns:
        None.

    Examples:
        ``token(path)`` permits an update based on ``HEAD``.
    """
    path.write_text(
        json.dumps({"repository": DEFAULT_REPOSITORY, "branch": DEFAULT_BRANCH, "missing": head is None, "head": head})
        + "\n"
    )


def test_fetch_existing_head_is_immutable_and_validates_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fetch a manifest at the exact head and checkpoint it.

    Args:
        tmp_path: Test directory.
        monkeypatch: Replaces the gh subprocess.

    Returns:
        None.

    Examples:
        A valid remote manifest replaces local state and records its head.
    """
    path = tmp_path / "manifest.json"
    remote = ManifestStore(tmp_path / "remote.json")
    remote.save(Manifest())
    stub = GhStub(remote=(tmp_path / "remote.json").read_bytes())
    monkeypatch.setattr("scripts.site_archive.branch.subprocess.run", stub)
    fetch(path, tmp_path / "state-token.json")
    assert path.read_bytes() == stub.remote
    assert json.loads((tmp_path / "state-token.json").read_text())["head"] == HEAD


def test_fetch_absent_branch_is_explicit_and_writes_empty_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Represent an absent branch without creating a fake remote state.

    Args:
        tmp_path: Test directory.
        monkeypatch: Replaces the gh subprocess.

    Returns:
        None.

    Examples:
        A first run gets a missing token and a valid empty manifest.
    """
    stub = GhStub(head=None)
    monkeypatch.setattr("scripts.site_archive.branch.subprocess.run", stub)
    path = tmp_path / "manifest.json"
    fetch(path, tmp_path / "state-token.json")
    assert ManifestStore(path).load() == Manifest()
    assert json.loads((tmp_path / "state-token.json").read_text())["missing"] is True


def test_push_initial_commit_is_orphan_and_creates_ref_last(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Create the first branch commit with only the manifest file.

    Args:
        tmp_path: Test directory.
        monkeypatch: Replaces the gh subprocess.

    Returns:
        None.

    Examples:
        An absent branch receives an orphan commit and a final ref creation.
    """
    path, _ = manifest_bytes(tmp_path)
    state = tmp_path / "state-token.json"
    token(state, None)
    stub = GhStub(head=None)
    monkeypatch.setattr("scripts.site_archive.branch.subprocess.run", stub)
    push(path, state)
    write_calls = [(command, value) for command, value in stub.calls if value is not None]
    assert write_calls
    assert all("--input" in command and command[command.index("--input") + 1] == "-" for command, _ in write_calls)
    payloads = [json.loads(value) for command, value in stub.calls if value and "--method" in command]
    commit = next(value for value in payloads if value.get("parents") == [])
    assert commit["message"].endswith("Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>")
    assert any(value.get("ref") == "refs/heads/site-archive-data" for value in payloads)
    assert json.loads(state.read_text())["head"] == COMMIT


def test_push_updates_existing_branch_without_force(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Create a child commit and PATCH the existing ref non-forcefully.

    Args:
        tmp_path: Test directory.
        monkeypatch: Replaces the gh subprocess.

    Returns:
        None.

    Examples:
        A changed manifest advances an existing data branch.
    """
    path, content = manifest_bytes(tmp_path)
    state = tmp_path / "state-token.json"
    token(state)
    stub = GhStub(remote=b"older manifest")
    monkeypatch.setattr("scripts.site_archive.branch.subprocess.run", stub)
    push(path, state)
    assert path.read_bytes() == content
    assert json.loads(state.read_text())["head"] == COMMIT
    patch_command, patch_input = next(
        (command, value) for command, value in stub.calls if command[2].endswith("/git/refs/heads/site-archive-data")
    )
    assert json.loads(patch_input or "{}")["force"] is False
    assert "--input" in patch_command


def test_push_concurrent_nonforce_rejection_preserves_local_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Leave local state intact when GitHub rejects a concurrent update.

    Args:
        tmp_path: Test directory.
        monkeypatch: Replaces the gh subprocess.

    Returns:
        None.

    Examples:
        A non-fast-forward response does not roll back or overwrite local data.
    """

    class ConcurrentWriter(GhStub):
        """Reject the final non-forced ref update."""

        def __call__(self, command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            """Simulate another writer advancing the branch.

            Args:
                command: gh arguments.
                kwargs: Subprocess options.

            Returns:
                Mocked API response.

            Examples:
                A PATCH receives an explicit non-fast-forward rejection.
            """
            if command[2].endswith("/git/refs/heads/site-archive-data"):
                payload = json.loads(kwargs.get("input") or "{}")
                assert payload["force"] is False
                return self.fail("gh: Update is not a fast forward (HTTP 422)")
            return super().__call__(command, **kwargs)

    path, content = manifest_bytes(tmp_path)
    state = tmp_path / "state-token.json"
    token(state)
    original_token = state.read_bytes()
    stub = ConcurrentWriter(remote=b"older manifest")
    monkeypatch.setattr("scripts.site_archive.branch.subprocess.run", stub)
    with pytest.raises(BranchPersistenceError, match="cannot update branch"):
        push(path, state)
    assert path.read_bytes() == content
    assert state.read_bytes() == original_token


def test_push_refuses_stale_head_before_creating_objects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a concurrent writer without creating blobs or commits.

    Args:
        tmp_path: Test directory.
        monkeypatch: Replaces the gh subprocess.

    Returns:
        None.

    Examples:
        A changed remote ref is a visible conflict.
    """
    path, _ = manifest_bytes(tmp_path)
    state = tmp_path / "state-token.json"
    token(state)
    stub = GhStub(head="e" * 40)
    monkeypatch.setattr("scripts.site_archive.branch.subprocess.run", stub)
    with pytest.raises(BranchPersistenceError, match="stale"):
        push(path, state)
    assert not any("/git/blobs" in command[2] for command, _ in stub.calls)


def test_push_identical_bytes_does_not_create_empty_commit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid a commit when the remote manifest bytes are unchanged.

    Args:
        tmp_path: Test directory.
        monkeypatch: Replaces the gh subprocess.

    Returns:
        None.

    Examples:
        Re-running a successful checkpoint is idempotent.
    """
    path, content = manifest_bytes(tmp_path)
    state = tmp_path / "state-token.json"
    token(state)
    stub = GhStub(remote=content)
    monkeypatch.setattr("scripts.site_archive.branch.subprocess.run", stub)
    push(path, state)
    assert not any("/git/blobs" in command[2] for command, _ in stub.calls)


def test_fetch_reads_large_manifest_through_immutable_blob(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Read a contents response that requires the Git blob endpoint.

    Args:
        tmp_path: Test directory.
        monkeypatch: Replaces the gh subprocess.

    Returns:
        None.

    Examples:
        A contents ``encoding: none`` response still fetches the exact blob.
    """
    remote = ManifestStore(tmp_path / "remote.json")
    remote.save(Manifest())
    remote_bytes = (tmp_path / "remote.json").read_bytes()

    class LargeContents(GhStub):
        """Return a SHA-only contents response."""

        def __call__(self, command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            """Serve the manifest through the immutable blob API.

            Args:
                command: gh arguments.
                kwargs: Subprocess options.

            Returns:
                Mocked API response.

            Examples:
                Large files use ``encoding: none`` in Contents API responses.
            """
            self.calls.append((command, kwargs.get("input")))
            if command[2].startswith("repos/palewire/palewi.re/contents/manifest.json"):
                return self.ok({"encoding": "none", "content": "", "sha": BLOB})
            if command[2].endswith(f"/git/blobs/{BLOB}"):
                return self.ok({"encoding": "base64", "content": base64.b64encode(remote_bytes).decode()})
            return super().__call__(command, **kwargs)

    stub = LargeContents()
    monkeypatch.setattr("scripts.site_archive.branch.subprocess.run", stub)
    path = tmp_path / "manifest.json"
    fetch(path, tmp_path / "state-token.json")
    assert path.read_bytes() == remote_bytes
    assert any(command[2].endswith(f"/git/blobs/{BLOB}") for command, _ in stub.calls)


def test_fetch_refuses_unsaved_local_manifest_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Protect local edits rather than replacing them during fetch.

    Args:
        tmp_path: Test directory.
        monkeypatch: Replaces the gh subprocess.

    Returns:
        None.

    Examples:
        A differing local file directs reconciliation to a fresh path.
    """
    path = tmp_path / "manifest.json"
    path.write_text("local unsaved changes")
    stub = GhStub(remote=b"remote")
    monkeypatch.setattr("scripts.site_archive.branch.subprocess.run", stub)
    with pytest.raises(BranchPersistenceError, match="fresh path"):
        fetch(path, tmp_path / "state-token.json")
    assert path.read_text() == "local unsaved changes"


def test_manifest_and_token_paths_must_differ(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject aliased manifest and token destinations before API access.

    Args:
        tmp_path: Test directory.
        monkeypatch: Replaces the gh subprocess.

    Returns:
        None.

    Examples:
        ``fetch(path, path)`` is rejected before any write.
    """
    stub = GhStub()
    monkeypatch.setattr("scripts.site_archive.branch.subprocess.run", stub)
    path = tmp_path / "same.json"
    with pytest.raises(BranchPersistenceError, match="must be different"):
        fetch(path, path)
    assert stub.calls == []


def test_push_rejects_malformed_token_without_touching_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject malformed optimistic-lock state before API writes.

    Args:
        tmp_path: Test directory.
        monkeypatch: Replaces the gh subprocess.

    Returns:
        None.

    Examples:
        A malformed token cannot silently reset persistence state.
    """
    path, content = manifest_bytes(tmp_path)
    state = tmp_path / "state-token.json"
    state.write_text("{}")
    stub = GhStub()
    monkeypatch.setattr("scripts.site_archive.branch.subprocess.run", stub)
    with pytest.raises(BranchPersistenceError, match="malformed"):
        push(path, state)
    assert path.read_bytes() == content
    assert stub.calls == []


def test_fetch_permission_error_is_not_treated_as_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Surface auth failures instead of initializing an empty branch.

    Args:
        tmp_path: Test directory.
        monkeypatch: Replaces the gh subprocess.

    Returns:
        None.

    Examples:
        A 403 ref response fails the fetch command.
    """

    class Forbidden(GhStub):
        """Return a permission failure for the branch ref."""

        def __call__(self, command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            """Return a forbidden response after repository access.

            Args:
                command: gh arguments.
                kwargs: Subprocess options.

            Returns:
                Mocked response.

            Examples:
                The branch lookup remains distinguishable from a 404.
            """
            if command[2].endswith("/git/ref/heads/site-archive-data"):
                return self.fail("gh: Forbidden (HTTP 403)")
            return super().__call__(command, **kwargs)

    monkeypatch.setattr("scripts.site_archive.branch.subprocess.run", Forbidden())
    with pytest.raises(BranchPersistenceError, match="403"):
        fetch(tmp_path / "manifest.json", tmp_path / "state-token.json")


def test_fetch_repository_not_found_is_not_treated_as_missing_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Require repository metadata before interpreting a ref 404.

    Args:
        tmp_path: Test directory.
        monkeypatch: Replaces the gh subprocess.

    Returns:
        None.

    Examples:
        A repository-level 404 remains an access failure, not an empty branch.
    """

    class MissingRepository(GhStub):
        """Return a repository-level not-found response."""

        def __call__(self, command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            """Reject repository metadata lookup.

            Args:
                command: gh arguments.
                kwargs: Subprocess options.

            Returns:
                Mocked response.

            Examples:
                The branch ref is never interpreted.
            """
            if command[2] == "repos/palewire/palewi.re":
                return self.fail("gh: Not Found (HTTP 404)")
            return super().__call__(command, **kwargs)

    monkeypatch.setattr("scripts.site_archive.branch.subprocess.run", MissingRepository())
    with pytest.raises(BranchPersistenceError, match="cannot access repository"):
        fetch(tmp_path / "manifest.json", tmp_path / "state-token.json")
    assert not (tmp_path / "manifest.json").exists()
    assert not (tmp_path / "state-token.json").exists()


def test_cli_rejects_other_branch() -> None:
    """Keep persistence restricted to the dedicated data branch.

    Returns:
        None.

    Examples:
        A typo cannot redirect writes to another branch.
    """
    result = CliRunner().invoke(
        cli,
        ["fetch", "--path", "manifest.json", "--state-token", "state.json", "--branch", "main"],
    )
    assert result.exit_code != 0
    assert "site-archive-data" in result.output


def test_cli_registers_fetch_command(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Expose the advertised ``fetch`` command name in Click.

    Args:
        monkeypatch: Replaces the fetch implementation.
        tmp_path: Test directory.

    Returns:
        None.

    Examples:
        ``CliRunner`` can invoke ``fetch`` rather than ``fetch-command``.
    """
    calls: list[tuple[Path, Path, str, str]] = []

    def fake_fetch(path: Path, state_token: Path, repository: str, branch: str) -> None:
        """Record a CLI fetch invocation.

        Args:
            path: Manifest path.
            state_token: Token path.
            repository: Repository name.
            branch: Data branch.

        Returns:
            None.

        Examples:
            The command forwards every persistence option.
        """
        calls.append((path, state_token, repository, branch))

    monkeypatch.setattr("scripts.site_archive.branch.fetch", fake_fetch)
    result = CliRunner().invoke(
        cli,
        ["fetch", "--path", str(tmp_path / "manifest.json"), "--state-token", str(tmp_path / "state.json")],
    )
    assert result.exit_code == 0
    assert calls == [(tmp_path / "manifest.json", tmp_path / "state.json", DEFAULT_REPOSITORY, DEFAULT_BRANCH)]
