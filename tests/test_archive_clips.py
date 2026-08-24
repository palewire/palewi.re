"""Tests for the clip URL archiver."""

from pathlib import Path

import requests
from click.testing import CliRunner
from savepagenow import BlockedByRobots
from savepagenow.exceptions import TooManyRequests

from scripts import archive_clips


class FakeResponse:
    """Minimal response used by availability API tests."""

    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        """Accept the fake response."""

    def json(self):
        """Return the configured JSON response."""
        return self.payload


def write_clips(path: Path, *, archive_metadata: str = "") -> None:
    """Write a minimal clip catalog."""
    path.write_text(
        "clips:\n"
        "- title: Example\n"
        "  type: story\n"
        "  date: '2024-01-01'\n"
        "  url: https://example.com/story\n"
        f"{archive_metadata}",
        encoding="utf-8",
    )


def test_archive_reuses_existing_snapshot(tmp_path, monkeypatch):
    path = tmp_path / "clips.yaml"
    write_clips(path)
    monkeypatch.setattr(
        archive_clips,
        "lookup_existing_snapshot",
        lambda url: "http://web.archive.org/web/20240101000000/https://example.com/story",
    )

    result = CliRunner().invoke(archive_clips.cli, ["archive", "--path", str(path), "--delay", "0"])

    assert result.exit_code == 0
    assert "found existing snapshot" in result.output
    assert "archive_url: https://web.archive.org/web/20240101000000/https://example.com/story" in path.read_text()


def test_lookup_existing_snapshot_parses_availability_response(monkeypatch):
    monkeypatch.setattr(
        requests,
        "get",
        lambda *args, **kwargs: FakeResponse(
            {
                "archived_snapshots": {
                    "closest": {
                        "available": True,
                        "status": "200",
                        "url": "http://web.archive.org/web/20240101000000/https://example.com/story",
                    }
                }
            }
        ),
    )

    snapshot = archive_clips.lookup_existing_snapshot("https://example.com/story")

    assert snapshot == "https://web.archive.org/web/20240101000000/https://example.com/story"


def test_lookup_existing_snapshot_returns_none_when_unavailable(monkeypatch):
    monkeypatch.setattr(
        requests,
        "get",
        lambda *args, **kwargs: FakeResponse({"archived_snapshots": {}}),
    )

    assert archive_clips.lookup_existing_snapshot("https://example.com/story") is None


def test_capture_retries_temporary_error(monkeypatch):
    calls = 0

    def capture_page(url, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TooManyRequests("slow down")
        return "http://web.archive.org/web/20240101000000/https://example.com/story"

    monkeypatch.setenv("SAVEPAGENOW_ACCESS_KEY", "access")
    monkeypatch.setenv("SAVEPAGENOW_SECRET_KEY", "secret")
    monkeypatch.setattr(archive_clips.time, "sleep", lambda delay: None)

    snapshot = archive_clips.capture_with_retries(
        "https://example.com/story",
        retry_delay=0,
        capture_page=capture_page,
    )

    assert calls == 2
    assert snapshot.startswith("https://web.archive.org/")


def test_archive_record_accepts_direct_wayback_url():
    record = {"url": "http://web.archive.org/web/20240101000000/https://example.com/story"}

    outcome = archive_clips.archive_record(record, retry_delay=0)

    assert outcome == "already a Wayback URL"
    assert record["archive_url"].startswith("https://")


def test_archive_creates_snapshot_with_credentials(tmp_path, monkeypatch):
    path = tmp_path / "clips.yaml"
    write_clips(path)
    monkeypatch.setattr(archive_clips, "lookup_existing_snapshot", lambda url: None)
    monkeypatch.setenv("SAVEPAGENOW_ACCESS_KEY", "access")
    monkeypatch.setenv("SAVEPAGENOW_SECRET_KEY", "secret")
    monkeypatch.setattr(
        archive_clips,
        "capture_with_retries",
        lambda url, retry_delay: "https://web.archive.org/web/20240101000000/https://example.com/story",
    )

    result = CliRunner().invoke(archive_clips.cli, ["archive", "--path", str(path), "--delay", "0"])

    assert result.exit_code == 0
    assert "created snapshot" in result.output


def test_archive_records_robots_exemption(tmp_path, monkeypatch):
    path = tmp_path / "clips.yaml"
    write_clips(path)
    monkeypatch.setattr(archive_clips, "lookup_existing_snapshot", lambda url: None)
    monkeypatch.setattr(
        archive_clips,
        "capture_with_retries",
        lambda url, retry_delay: (_ for _ in ()).throw(BlockedByRobots("blocked")),
    )

    result = CliRunner().invoke(archive_clips.cli, ["archive", "--path", str(path), "--delay", "0"])

    assert result.exit_code == 0
    assert "robots-policy exemption" in result.output
    assert "archive_exemption:" in path.read_text()


def test_check_requires_archive_metadata(tmp_path):
    path = tmp_path / "clips.yaml"
    write_clips(path)

    missing = CliRunner().invoke(archive_clips.cli, ["check", "--path", str(path)])

    assert missing.exit_code == 1
    assert "1 clip URL(s) lack archive metadata" in missing.output

    write_clips(
        path,
        archive_metadata=("  archive_url: https://web.archive.org/web/20240101000000/https://example.com/story\n"),
    )
    complete = CliRunner().invoke(archive_clips.cli, ["check", "--path", str(path)])

    assert complete.exit_code == 0
    assert "All 1 clip URLs" in complete.output


def test_capture_requires_credentials(tmp_path, monkeypatch):
    path = tmp_path / "clips.yaml"
    write_clips(path)
    monkeypatch.setattr(archive_clips, "lookup_existing_snapshot", lambda url: None)
    monkeypatch.delenv("SAVEPAGENOW_ACCESS_KEY", raising=False)
    monkeypatch.delenv("SAVEPAGENOW_SECRET_KEY", raising=False)

    result = CliRunner().invoke(
        archive_clips.cli,
        ["archive", "--path", str(path), "--delay", "0"],
    )

    assert result.exit_code == 1
    assert "SAVEPAGENOW_ACCESS_KEY and SAVEPAGENOW_SECRET_KEY must be set" in result.output
