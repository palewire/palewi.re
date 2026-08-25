"""Tests for the offline new-content preservation review."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from scripts.preservation_review import cli


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def inventory(sources: list[dict]) -> dict:
    return {"version": 1, "sources": sources}


def source(url: str, origin_type: str, origin_id: str, location: str, *gap_codes: str) -> dict:
    return {
        "source_url": url,
        "current_reference": True,
        "origins": [{"origin_type": origin_type, "origin_id": origin_id, "location": location}],
        "gaps": [{"code": code} for code in gap_codes],
    }


def baseline(*records: dict[str, str]) -> dict:
    return {"version": 1, "known_gaps": list(records)}


def run_review(tmp_path: Path, report: dict, reviewed: dict):
    inventory_path = tmp_path / "inventory.json"
    baseline_path = tmp_path / "baseline.json"
    write_json(inventory_path, report)
    write_json(baseline_path, reviewed)
    return CliRunner().invoke(cli, ["--inventory", str(inventory_path), "--baseline", str(baseline_path)])


def test_review_reports_new_clip_with_wayback_action(tmp_path):
    result = run_review(
        tmp_path,
        inventory(
            [
                source(
                    "https://example.com/new-clip",
                    "clip",
                    "New clip",
                    "clips.yaml:url",
                    "wayback-missing",
                )
            ]
        ),
        baseline(),
    )

    assert result.exit_code == 1
    assert "NEW  wayback-missing  https://example.com/new-clip" in result.output
    assert "clip 'New clip' (clips.yaml:url)" in result.output
    assert "make archive-clips" in result.output


def test_review_reports_new_talk_and_post_media_with_backup_and_replica_actions(tmp_path):
    result = run_review(
        tmp_path,
        inventory(
            [
                source(
                    "https://vimeo.com/new-talk",
                    "talk",
                    "2026-08-25 New talk",
                    "video_url",
                    "local-media-untracked",
                ),
                source(
                    "https://example.com/new-post.mp4",
                    "post",
                    "new-post",
                    "video",
                    "local-media-untracked",
                ),
            ]
        ),
        baseline(),
    )

    assert result.exit_code == 1
    assert "talk '2026-08-25 New talk' (video_url)" in result.output
    assert "post 'new-post' (video)" in result.output
    assert "make media-archive-backup" in result.output
    assert "make media-archive-r2-sync" in result.output


def test_review_allows_a_specific_recorded_media_access_exemption(tmp_path):
    url = "https://private.example.com/recording"
    result = run_review(
        tmp_path,
        inventory([source(url, "talk", "2026-08-25 Private talk", "video_url", "local-media-untracked")]),
        baseline(
            {
                "source_url": url,
                "code": "local-media-untracked",
                "reason": "Recording requires a host account and may not be downloaded without bypassing access controls.",
            }
        ),
    )

    assert result.exit_code == 0, result.output
    assert "1 reviewed, 0 new." in result.output


def test_review_rejects_wayback_missing_baseline_exception(tmp_path):
    result = run_review(
        tmp_path,
        inventory([]),
        baseline(
            {
                "source_url": "https://example.com/clip",
                "code": "wayback-missing",
                "reason": "This must not bypass clip archiving.",
            }
        ),
    )

    assert result.exit_code == 1
    assert "Wayback gaps cannot be accepted" in result.output
