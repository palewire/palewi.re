"""Tests for the worktree-aware development server command."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from scripts import worktree


def test_run_server_reports_port_claims(monkeypatch: pytest.MonkeyPatch):
    class Process:
        stderr = iter(["Watching for file changes\n", "Error: That port is already in use.\n"])

        def wait(self):
            return 1

    monkeypatch.setattr(worktree.subprocess, "Popen", lambda *args, **kwargs: Process())

    assert worktree.run_server(8123) == (1, True)


def test_serve_retries_when_port_is_claimed(monkeypatch: pytest.MonkeyPatch):
    ports = iter([8100, 8101])
    attempts: list[int] = []

    def select_port(root: Path, excluded: set[int]) -> int:
        assert root == worktree.ROOT
        return next(ports)

    def run_server(port: int) -> tuple[int, bool]:
        attempts.append(port)
        return (1, True) if port == 8100 else (0, False)

    monkeypatch.setattr(worktree, "available_port", select_port)
    monkeypatch.setattr(worktree, "run_server", run_server)

    result = CliRunner().invoke(worktree.cli, ["serve"])

    assert result.exit_code == 0
    assert attempts == [8100, 8101]
    assert "retrying" in result.output


def test_serve_reports_when_no_ports_are_available(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(worktree, "available_port", lambda *_: (_ for _ in ()).throw(RuntimeError("No available port")))

    result = CliRunner().invoke(worktree.cli, ["serve"])

    assert result.exit_code == 1
    assert "No available port" in result.output
