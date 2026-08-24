"""Tests for shared template context."""

import subprocess
from unittest.mock import patch

from toolbox.context_processors import REPOSITORY_URL, _main_commit, repository


def test_repository_uses_heroku_commit():
    commit = "0123456789abcdef0123456789abcdef01234567"

    with patch.dict("os.environ", {"HEROKU_SLUG_COMMIT": commit}, clear=True):
        _main_commit.cache_clear()
        context = repository(None)

    assert context == {
        "repository_url": REPOSITORY_URL,
        "repository_commit": commit,
        "repository_commit_short": "0123456",
    }
    _main_commit.cache_clear()


def test_repository_uses_local_main_commit():
    completed = subprocess.CompletedProcess(
        args=["git", "rev-parse", "main"],
        returncode=0,
        stdout="abcdef1234567890\n",
    )

    with (
        patch.dict("os.environ", {}, clear=True),
        patch("toolbox.context_processors.subprocess.run", return_value=completed),
    ):
        _main_commit.cache_clear()
        context = repository(None)

    assert context["repository_commit"] == "abcdef1234567890"
    assert context["repository_commit_short"] == "abcdef1"
    _main_commit.cache_clear()


def test_repository_omits_invalid_commit(caplog):
    with patch.dict("os.environ", {"SOURCE_VERSION": "not-a-commit"}, clear=True):
        _main_commit.cache_clear()
        context = repository(None)

    assert context["repository_commit"] is None
    assert context["repository_commit_short"] is None
    assert "Ignoring invalid main branch commit" in caplog.text
    _main_commit.cache_clear()
