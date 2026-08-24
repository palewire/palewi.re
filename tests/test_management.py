"""Tests for management commands."""

from django.core.management import get_commands


def test_legacy_sync_commands_are_removed():
    commands = get_commands()
    assert "publishstatic" not in commands
    assert "syncgithub" not in commands
    assert "synctwitter" not in commands
