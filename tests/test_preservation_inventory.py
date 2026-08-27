"""Tests for the combined, read-only preservation report."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from scripts import preservation_inventory
from scripts.media_archive import manifest as manifest_mod
from scripts.media_archive.discovery import KIND_DIRECT, MediaCandidate, MediaOccurrence
from scripts.preservation_inventory import cli


def write_clips(path: Path) -> None:
    path.write_text(
        "clips:\n"
        "- title: Saved media page\n"
        "  type: story\n"
        "  date: '2024-01-01'\n"
        "  url: https://example.com/clip.mp4\n"
        "  archive_url: https://web.archive.org/web/20240101000000/https://example.com/clip.mp4\n",
        encoding="utf-8",
    )


def write_talks(path: Path) -> None:
    path.write_text(
        "talks:\n"
        "- title: Untracked talk\n"
        "  venue: Venue\n"
        "  location: City\n"
        "  date: '2024-01-02'\n"
        "  video_url: https://vimeo.com/123456\n",
        encoding="utf-8",
    )


def write_posts(path: Path) -> None:
    path.mkdir()
    (path / "2024-01-01--example.md").write_text(
        "---\n"
        "title: Example\n"
        "slug: example\n"
        'published_at: "2024-01-01T09:00:00-08:00"\n'
        "---\n"
        '<video src="https://example.com/clip.mp4"></video>\n',
        encoding="utf-8",
    )


def report_args(tmp_path: Path, *extra_args: str) -> list[str]:
    clips_path = tmp_path / "clips.yaml"
    talks_path = tmp_path / "talks.yaml"
    posts_path = tmp_path / "posts"
    write_clips(clips_path)
    write_talks(talks_path)
    write_posts(posts_path)
    return [
        "--clips-path",
        str(clips_path),
        "--talks-path",
        str(talks_path),
        "--posts-path",
        str(posts_path),
        *extra_args,
    ]


def test_report_marks_media_untracked_without_archive_root(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, report_args(tmp_path))

    assert result.exit_code == 0, result.output
    assert "Preservation inventory: 2 source URL(s), 2 current, 2 gap(s)." in result.output
    assert "LOCAL-MEDIA-UNTRACKED" in result.output


def test_inventory_marks_committed_static_media_as_site_asset(tmp_path, monkeypatch):
    asset = tmp_path / "coltrane" / "static" / "img" / "example.mp4"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"video")
    monkeypatch.setattr(preservation_inventory, "REPO_ROOT", tmp_path)
    candidate = MediaCandidate(
        url="https://palewi.re/static/img/example.mp4",
        kind=KIND_DIRECT,
        occurrences=(
            MediaOccurrence(
                origin_type="post",
                origin_id="example",
                location="video>source",
                raw_url="/static/img/example.mp4",
            ),
        ),
    )

    report = preservation_inventory.build_inventory(
        clips=[],
        candidates=[candidate],
        manifest=None,
        archive_root_provided=False,
        manifest_found=False,
    )

    source = report["sources"][0]
    assert source["local_media"]["status"] == "site-asset"
    assert source["gaps"] == []


def test_report_joins_clip_and_media_records_and_writes_stable_json(tmp_path):
    archive_root = tmp_path / "archive"
    archive_root.mkdir()
    current_entry = manifest_mod.ManifestEntry(
        source_url="https://example.com/clip.mp4",
        kind="direct",
        occurrences=[
            {
                "origin_type": "post",
                "origin_id": "old-example",
                "location": "video",
                "raw_url": "https://example.com/clip.mp4",
            }
        ],
        status=manifest_mod.STATUS_SUCCESS,
        attempts=2,
        output_filename="direct/clip.mp4",
        size_bytes=12,
        sha256="abc123",
        last_verified_at="2026-08-25T00:00:00+00:00",
        updated_at="2026-08-24T00:00:00+00:00",
    )
    historical_entry = manifest_mod.ManifestEntry(
        source_url="https://example.com/removed.mp3",
        kind="direct",
        occurrences=[],
        status=manifest_mod.STATUS_SUCCESS,
        last_verified_at="2026-08-25T00:00:00+00:00",
    )
    manifest_mod.write_manifest(
        archive_root,
        manifest_mod.Manifest(
            entries={
                current_entry.source_url: current_entry,
                historical_entry.source_url: historical_entry,
            }
        ),
    )
    output_path = tmp_path / "inventory.json"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        report_args(
            tmp_path,
            "--archive-root",
            str(archive_root),
            "--json-output",
            str(output_path),
        ),
    )

    assert result.exit_code == 0, result.output
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["version"] == 1
    assert report["media_manifest"] == {"archive_root_provided": True, "manifest_found": True}
    assert [source["source_url"] for source in report["sources"]] == [
        "https://example.com/clip.mp4",
        "https://example.com/removed.mp3",
        "https://vimeo.com/123456",
    ]

    current = report["sources"][0]
    assert current["classifications"] == ["media:direct", "webpage"]
    assert current["preservation_methods"] == ["wayback", "local-media"]
    assert current["wayback"]["status"] == "snapshot"
    assert current["local_media"]["status"] == "success"
    assert current["local_media"]["last_attempt_at"] == "2026-08-24T00:00:00+00:00"
    assert current["local_media"]["verification_status"] == "verified"
    assert current["gaps"] == []
    assert {origin["origin_id"] for origin in current["origins"]} == {"Saved media page", "example", "old-example"}

    historical = report["sources"][1]
    assert historical["current_reference"] is False
    assert historical["classifications"] == ["media:direct"]
    assert historical["local_media"]["status"] == "success"

    untracked = report["sources"][2]
    assert untracked["local_media"]["status"] == "untracked"
    assert untracked["gaps"][0]["code"] == "local-media-untracked"


def test_report_keeps_unknown_manifest_status_visible_as_a_gap(tmp_path):
    archive_root = tmp_path / "archive"
    archive_root.mkdir()
    entry = manifest_mod.ManifestEntry(
        source_url="https://vimeo.com/123456",
        kind="vimeo",
        occurrences=[],
        status="unexpected",
    )
    manifest_mod.write_manifest(archive_root, manifest_mod.Manifest(entries={entry.source_url: entry}))

    runner = CliRunner()
    result = runner.invoke(cli, report_args(tmp_path, "--archive-root", str(archive_root)))

    assert result.exit_code == 0, result.output
    assert "LOCAL-MEDIA-INVALID-STATUS" in result.output


def test_report_surfaces_invalid_manifest_as_a_click_error(tmp_path):
    archive_root = tmp_path / "archive"
    archive_root.mkdir()
    manifest_mod.manifest_path(archive_root).write_text(
        json.dumps(
            {
                "entries": {
                    "https://vimeo.com/123456": {
                        "source_url": "https://vimeo.com/123456",
                        "kind": "vimeo",
                        "occurrences": None,
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(cli, report_args(tmp_path, "--archive-root", str(archive_root)))

    assert result.exit_code == 1
    assert "occurrences" in result.output
