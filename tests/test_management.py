"""Tests for management commands."""

from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command, get_commands


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


# ---------------------------------------------------------------------------
# Integration tests for the compilescss management command
# ---------------------------------------------------------------------------


class _FakeAppConfig:
    """Minimal AppConfig stand-in whose 'path' points at a tmp directory."""

    def __init__(self, path):
        self.path = str(path)


@pytest.fixture()
def scss_app(tmp_path):
    """Return a fake app whose static/ folder has one entry and two partials."""
    static = tmp_path / "static"
    static.mkdir()
    (static / "styles.scss").write_text("body { color: red; }\n")
    (static / "_partial.scss").write_text("$color: red;\n")
    (static / "_another.scss").write_text("p { margin: 0; }\n")
    return tmp_path


def test_compilescss_compiles_entry_point(scss_app):
    """compilescss writes CSS for non-partial SCSS and skips partial files."""
    app_cfg = _FakeAppConfig(scss_app)
    with patch("django.apps.apps.get_app_configs", return_value=[app_cfg]):
        out = StringIO()
        call_command("compilescss", verbosity=2, stdout=out)

    css_file = scss_app / "static" / "styles.css"
    assert css_file.exists(), "CSS file should be written next to the SCSS source"
    css_content = css_file.read_text()
    assert "color" in css_content, "Compiled CSS should contain the colour rule"

    # Partials must not be compiled to their own CSS files
    assert not (scss_app / "static" / "_partial.css").exists()
    assert not (scss_app / "static" / "_another.css").exists()

    output = out.getvalue()
    assert "styles.scss" in output
    assert "Successfully compiled 1 SCSS file" in output


def test_compilescss_skips_dirs_without_static(tmp_path):
    """compilescss does not error when an app has no static/ directory."""
    app_cfg = _FakeAppConfig(tmp_path)  # no static/ sub-dir
    with patch("django.apps.apps.get_app_configs", return_value=[app_cfg]):
        out = StringIO()
        call_command("compilescss", verbosity=1, stdout=out)
    assert "Successfully compiled 0 SCSS file" in out.getvalue()


def test_compilescss_surfaces_sass_errors(scss_app):
    """compilescss propagates libsass compile errors so they are not silently lost."""
    import sass

    (scss_app / "static" / "bad.scss").write_text("body { color: @invalid; }\n")
    app_cfg = _FakeAppConfig(scss_app)
    with patch("django.apps.apps.get_app_configs", return_value=[app_cfg]):
        with pytest.raises(sass.CompileError):
            call_command("compilescss", verbosity=0)
