from pathlib import Path

import pytest

from project import worktree
from project.worktree import DEFAULT_DATABASE_NAME, available_port, candidate_ports, database_name, default_database_url


def test_main_checkout_uses_default_database(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()

    assert database_name(tmp_path) == DEFAULT_DATABASE_NAME
    assert default_database_url(tmp_path) == "postgres://postgres@localhost/palewire"


def test_linked_worktree_uses_isolated_database(tmp_path: Path) -> None:
    (tmp_path / ".git").write_text("gitdir: /tmp/example\n")

    name = database_name(tmp_path)

    assert name.startswith("palewire_")
    assert name != DEFAULT_DATABASE_NAME
    assert len(name) <= 63
    assert default_database_url(tmp_path).endswith(f"/{name}")


def test_long_worktree_names_produce_valid_database_names(tmp_path: Path) -> None:
    root = tmp_path / ("A branch with punctuation!" * 6)
    root.mkdir()
    (root / ".git").write_text("gitdir: /tmp/example\n")

    name = database_name(root)

    assert len(name) <= 63
    assert name.replace("_", "").isalnum()


def test_available_port_skips_occupied_and_excluded_ports(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    first, second, third = list(candidate_ports(tmp_path))[:3]
    monkeypatch.setattr(worktree, "port_is_available", lambda port: port in {first, third})

    assert available_port(tmp_path, {first}) == third
    assert second != third


def test_available_port_reports_exhausted_range(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(worktree, "port_is_available", lambda port: False)

    with pytest.raises(RuntimeError, match="No available port found"):
        available_port(tmp_path)
