import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from project import worktree
from project.worktree import (
    DEFAULT_DATABASE_NAME,
    POSTGRES_IDENTIFIER_LIMIT,
    available_port,
    candidate_ports,
    database_name,
    default_database_url,
    django_test_database_name,
)


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


@pytest.mark.parametrize(
    ("base_name", "expected"),
    [
        ("palewire", "test_palewire"),
        ("a" * 58, f"test_{'a' * 58}"),
        ("", "test_database"),
        ("Odd database name! 🐘", "test_odd_database_name"),
    ],
)
def test_test_database_name_handles_names_that_fit(base_name: str, expected: str) -> None:
    name = django_test_database_name(base_name)

    assert name == expected
    assert len(name) <= POSTGRES_IDENTIFIER_LIMIT
    assert re.fullmatch(r"[a-z0-9_]+", name)


def test_test_database_name_hashes_name_one_character_over_limit() -> None:
    name = django_test_database_name("a" * 59)

    assert len(name) == POSTGRES_IDENTIFIER_LIMIT
    assert name.startswith(f"test_{'a' * 49}_")
    assert re.fullmatch(r"[a-z0-9_]+", name)


def test_long_test_database_names_with_shared_prefix_remain_distinct() -> None:
    prefix = "palewire_" + "same_prefix_" * 10
    first = django_test_database_name(f"{prefix}first")
    second = django_test_database_name(f"{prefix}second")

    assert first != second
    assert len(first) == len(second) == POSTGRES_IDENTIFIER_LIMIT
    assert re.fullmatch(r"[a-z0-9_]+", first)
    assert re.fullmatch(r"[a-z0-9_]+", second)


def test_test_database_name_is_deterministic() -> None:
    base_name = "palewire_" + "long_worktree_" * 10

    assert django_test_database_name(base_name) == django_test_database_name(base_name)


def test_long_linked_worktree_has_safe_test_database_name(tmp_path: Path) -> None:
    root = tmp_path / "palewire-retire-legacy-scraper-models-and-database-tables"
    root.mkdir()
    (root / ".git").write_text("gitdir: /tmp/example\n")

    development_name = database_name(root)
    test_name = django_test_database_name(development_name)

    assert len(development_name) == POSTGRES_IDENTIFIER_LIMIT
    assert len(test_name) == POSTGRES_IDENTIFIER_LIMIT
    assert re.fullmatch(r"[a-z0-9_]+", test_name)


def test_database_url_override_configures_safe_django_test_name() -> None:
    base_name = "palewire_" + "issue_357_worktree_" * 5
    env = os.environ.copy()
    env["DATABASE_URL"] = f"postgres://postgres@localhost/{base_name}"
    command = (
        "from project.settings import DATABASES; "
        "print(DATABASES['default']['NAME']); "
        "print(DATABASES['default']['TEST']['NAME'])"
    )

    result = subprocess.run(
        [sys.executable, "-c", command],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )
    configured_name, configured_test_name = result.stdout.splitlines()

    assert configured_name == base_name
    assert configured_test_name == django_test_database_name(base_name)
    assert len(configured_test_name) <= POSTGRES_IDENTIFIER_LIMIT
    assert re.fullmatch(r"[a-z0-9_]+", configured_test_name)


def test_available_port_skips_occupied_and_excluded_ports(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    first, second, third = list(candidate_ports(tmp_path))[:3]
    monkeypatch.setattr(worktree, "port_is_available", lambda port: port in {first, third})

    assert available_port(tmp_path, {first}) == third
    assert second != third


def test_available_port_reports_exhausted_range(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(worktree, "port_is_available", lambda port: False)

    with pytest.raises(RuntimeError, match="No available port found"):
        available_port(tmp_path)
