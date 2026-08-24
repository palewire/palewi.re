from pathlib import Path

import pytest

from project import worktree
from project.worktree import available_port, candidate_ports


def test_available_port_skips_occupied_and_excluded_ports(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    first, second, third = list(candidate_ports(tmp_path))[:3]
    monkeypatch.setattr(worktree, "port_is_available", lambda port: port in {first, third})

    assert available_port(tmp_path, {first}) == third
    assert second != third


def test_available_port_reports_exhausted_range(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(worktree, "port_is_available", lambda port: False)

    with pytest.raises(RuntimeError, match="No available port found"):
        available_port(tmp_path)
