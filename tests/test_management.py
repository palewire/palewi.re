"""Tests for management commands."""

from django.core.management import get_commands


def test_legacy_sync_commands_are_removed():
    commands = get_commands()
    assert "publishstatic" not in commands
    assert "syncgithub" not in commands
    assert "synctwitter" not in commands


def test_legacy_stylesheet_command_is_removed():
    """Stylesheets are not managed by Django."""
    commands = get_commands()
    assert "compilescss" not in commands
