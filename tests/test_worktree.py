from pathlib import Path

from project.worktree import DEFAULT_DATABASE_NAME, database_name, default_database_url


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
