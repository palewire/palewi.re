from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from project.worktree import database_name
from scripts import worktree


def test_drop_database_rejects_remote_server(monkeypatch: pytest.MonkeyPatch) -> None:
    name = database_name(worktree.ROOT)
    monkeypatch.setenv("DATABASE_URL", f"postgres://example.com/{name}")

    with pytest.raises(click.ClickException, match="outside the local PostgreSQL server"):
        worktree.validate_local_drop_target()


def test_drop_database_rejects_remote_query_host(monkeypatch: pytest.MonkeyPatch) -> None:
    name = database_name(worktree.ROOT)
    monkeypatch.setenv("DATABASE_URL", f"postgres:///local/{name}?host=example.com")

    with pytest.raises(click.ClickException, match="outside the local PostgreSQL server"):
        worktree.validate_local_drop_target()


def test_serve_retries_when_port_is_claimed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
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
