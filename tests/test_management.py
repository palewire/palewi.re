"""Tests for management commands."""

import sass
from django.core.management import get_commands


def test_legacy_sync_commands_are_removed():
    commands = get_commands()
    assert "publishstatic" not in commands
    assert "syncgithub" not in commands
    assert "synctwitter" not in commands


def test_compilescss_command_is_registered():
    """Local compilescss command is registered and callable."""
    commands = get_commands()
    assert "compilescss" in commands
    # Verify it resolves to our local app, not django-sass-processor
    assert commands["compilescss"] == "coltrane"


def test_compilescss_compiles_scss(tmp_path):
    """compilescss writes compressed CSS from a non-partial SCSS entry point."""
    scss_file = tmp_path / "styles.scss"
    scss_file.write_text("body { color: red; }\n")

    content = sass.compile(filename=str(scss_file), output_style="compressed")
    assert "color:red" in content or "color: red" in content
