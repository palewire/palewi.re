"""Tests for management commands."""

from unittest.mock import patch

import pytest
from django.core.management import call_command, get_commands
from django.core.management.base import CommandError
from django.test import override_settings


def test_legacy_sync_commands_are_removed():
    commands = get_commands()
    assert "syncgithub" not in commands
    assert "synctwitter" not in commands


@pytest.mark.django_db
def test_publishstatic_raises_when_static_root_missing(tmp_path):
    """publishstatic raises CommandError when STATIC_ROOT does not exist."""
    nonexistent = str(tmp_path / "does_not_exist")
    with override_settings(STATIC_ROOT=nonexistent):
        with pytest.raises(CommandError, match="Static directory does not exist"):
            call_command("publishstatic")


@pytest.mark.django_db
def test_publishstatic_calls_s3cmd_when_root_exists(tmp_path):
    """publishstatic invokes s3cmd when STATIC_ROOT is present."""
    static_dir = tmp_path / "collected_static"
    static_dir.mkdir()

    with override_settings(STATIC_ROOT=str(static_dir), AWS_BUCKET_NAME="test-bucket"):
        with patch("subprocess.call") as mock_call:
            call_command("publishstatic")
            assert mock_call.called
            cmd_arg = mock_call.call_args[0][0]
            assert "s3cmd" in cmd_arg
            assert "test-bucket" in cmd_arg
