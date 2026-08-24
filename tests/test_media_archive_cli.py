"""Tests for the media archive Click commands."""

from pathlib import Path

from click.testing import CliRunner

from scripts.media_archive import cli as cli_module
from scripts.media_archive import downloader
from scripts.media_archive import manifest as manifest_mod


def write_talks(path: Path) -> None:
    path.write_text(
        "talks:\n"
        "- title: A Talk\n"
        "  venue: V\n"
        "  location: L\n"
        "  date: '2024-01-01'\n"
        "  video_url: https://vimeo.com/123456\n",
        encoding="utf-8",
    )


def write_posts(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "2024-01-01--example-post.md").write_text(
        "---\n"
        "title: Example post\n"
        "slug: example-post\n"
        'published_at: "2024-01-01T09:00:00-08:00"\n'
        "---\n"
        '<video src="https://example.com/clip.mp4"></video>\n',
        encoding="utf-8",
    )


def run_inventory(tmp_path, extra_args=()):
    talks_path = tmp_path / "talks.yaml"
    posts_path = tmp_path / "posts"
    write_talks(talks_path)
    write_posts(posts_path)
    runner = CliRunner()
    args = ["inventory", "--talks-path", str(talks_path), "--posts-path", str(posts_path), *extra_args]
    return runner.invoke(cli_module.cli, args)


def test_inventory_reports_counts(tmp_path):
    result = run_inventory(tmp_path)
    assert result.exit_code == 0
    assert "Discovered 2 unique media candidate(s)" in result.output
    assert "Referenced by talks: 1" in result.output
    assert "Referenced by posts: 1" in result.output


def test_inventory_writes_json_output(tmp_path):
    json_path = tmp_path / "candidates.json"
    result = run_inventory(tmp_path, extra_args=["--json-output", str(json_path)])
    assert result.exit_code == 0
    import json

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert len(payload) == 2
    assert {"url", "kind", "occurrences"} <= set(payload[0])


def test_inventory_reports_content_errors_as_click_exception(tmp_path):
    talks_path = tmp_path / "talks.yaml"
    posts_path = tmp_path / "posts"
    talks_path.write_text("talks:\n- venue: V\n  location: L\n  date: '2024-01-01'\n", encoding="utf-8")
    posts_path.mkdir()

    runner = CliRunner()
    result = runner.invoke(
        cli_module.cli,
        ["inventory", "--talks-path", str(talks_path), "--posts-path", str(posts_path)],
    )

    assert result.exit_code == 1


def test_backup_requires_archive_root(tmp_path):
    talks_path = tmp_path / "talks.yaml"
    posts_path = tmp_path / "posts"
    write_talks(talks_path)
    write_posts(posts_path)

    runner = CliRunner()
    result = runner.invoke(
        cli_module.cli,
        ["backup", "--talks-path", str(talks_path), "--posts-path", str(posts_path)],
    )

    assert result.exit_code == 1
    assert "An archive root is required" in result.output


def test_backup_refuses_archive_root_inside_repository(tmp_path):
    talks_path = tmp_path / "talks.yaml"
    posts_path = tmp_path / "posts"
    write_talks(talks_path)
    write_posts(posts_path)
    inside_repo_root = cli_module.REPO_ROOT / "some-archive-dir"

    runner = CliRunner()
    result = runner.invoke(
        cli_module.cli,
        [
            "backup",
            "--archive-root",
            str(inside_repo_root),
            "--talks-path",
            str(talks_path),
            "--posts-path",
            str(posts_path),
        ],
    )

    assert result.exit_code == 1
    assert "Refusing to store media under the repository" in result.output


def _fake_download_success(url, kind, archive_root):
    output_dir = archive_root / kind
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "file.bin"
    output_path.write_bytes(b"fake bytes")
    return downloader.DownloadOutcome(
        status="success",
        extractor="Fake",
        media_id="file",
        output_filename=str(output_path.relative_to(archive_root)),
        size_bytes=output_path.stat().st_size,
    )


def _fake_download_failure(url, kind, archive_root):
    return downloader.DownloadOutcome(status="failed", error="boom")


def test_backup_downloads_pending_candidates(tmp_path, monkeypatch):
    talks_path = tmp_path / "talks.yaml"
    posts_path = tmp_path / "posts"
    write_talks(talks_path)
    write_posts(posts_path)
    archive_root = tmp_path / "archive"
    monkeypatch.setattr(cli_module, "download_candidate", _fake_download_success)
    monkeypatch.setattr(cli_module, "ffmpeg_available", lambda: True)

    runner = CliRunner()
    result = runner.invoke(
        cli_module.cli,
        [
            "backup",
            "--archive-root",
            str(archive_root),
            "--talks-path",
            str(talks_path),
            "--posts-path",
            str(posts_path),
            "--delay",
            "0",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "2 succeeded, 0 failed" in result.output
    manifest = manifest_mod.load_manifest(archive_root)
    assert len(manifest.entries) == 2
    for entry in manifest.entries.values():
        assert entry.status == manifest_mod.STATUS_SUCCESS
        assert entry.sha256 is not None


def test_backup_records_failures_and_exits_nonzero(tmp_path, monkeypatch):
    talks_path = tmp_path / "talks.yaml"
    posts_path = tmp_path / "posts"
    write_talks(talks_path)
    write_posts(posts_path)
    archive_root = tmp_path / "archive"
    monkeypatch.setattr(cli_module, "download_candidate", _fake_download_failure)
    monkeypatch.setattr(cli_module, "ffmpeg_available", lambda: True)

    runner = CliRunner()
    result = runner.invoke(
        cli_module.cli,
        [
            "backup",
            "--archive-root",
            str(archive_root),
            "--talks-path",
            str(talks_path),
            "--posts-path",
            str(posts_path),
            "--delay",
            "0",
        ],
    )

    assert result.exit_code == 1
    manifest = manifest_mod.load_manifest(archive_root)
    assert all(entry.status == manifest_mod.STATUS_FAILED for entry in manifest.entries.values())
    assert all(entry.error == "boom" for entry in manifest.entries.values())


def test_backup_skips_already_successful_entries(tmp_path, monkeypatch):
    talks_path = tmp_path / "talks.yaml"
    posts_path = tmp_path / "posts"
    write_talks(talks_path)
    write_posts(posts_path)
    archive_root = tmp_path / "archive"

    calls = []

    def counting_download(url, kind, root):
        calls.append(url)
        return _fake_download_success(url, kind, root)

    monkeypatch.setattr(cli_module, "download_candidate", counting_download)
    monkeypatch.setattr(cli_module, "ffmpeg_available", lambda: True)
    runner = CliRunner()
    common_args = [
        "backup",
        "--archive-root",
        str(archive_root),
        "--talks-path",
        str(talks_path),
        "--posts-path",
        str(posts_path),
        "--delay",
        "0",
    ]

    first = runner.invoke(cli_module.cli, common_args)
    assert first.exit_code == 0
    assert len(calls) == 2

    second = runner.invoke(cli_module.cli, common_args)
    assert second.exit_code == 0
    assert "Nothing to back up" in second.output
    assert len(calls) == 2  # no new calls


def test_backup_force_redownloads_successful_entries(tmp_path, monkeypatch):
    talks_path = tmp_path / "talks.yaml"
    posts_path = tmp_path / "posts"
    write_talks(talks_path)
    write_posts(posts_path)
    archive_root = tmp_path / "archive"
    calls = []

    def counting_download(url, kind, root):
        calls.append(url)
        return _fake_download_success(url, kind, root)

    monkeypatch.setattr(cli_module, "download_candidate", counting_download)
    monkeypatch.setattr(cli_module, "ffmpeg_available", lambda: True)
    runner = CliRunner()
    base_args = [
        "backup",
        "--archive-root",
        str(archive_root),
        "--talks-path",
        str(talks_path),
        "--posts-path",
        str(posts_path),
        "--delay",
        "0",
    ]

    runner.invoke(cli_module.cli, base_args)
    assert len(calls) == 2

    runner.invoke(cli_module.cli, [*base_args, "--force"])
    assert len(calls) == 4


def test_backup_retry_failed_flag_controls_reattempts(tmp_path, monkeypatch):
    talks_path = tmp_path / "talks.yaml"
    posts_path = tmp_path / "posts"
    write_talks(talks_path)
    write_posts(posts_path)
    archive_root = tmp_path / "archive"
    monkeypatch.setattr(cli_module, "download_candidate", _fake_download_failure)
    monkeypatch.setattr(cli_module, "ffmpeg_available", lambda: True)
    runner = CliRunner()
    base_args = [
        "backup",
        "--archive-root",
        str(archive_root),
        "--talks-path",
        str(talks_path),
        "--posts-path",
        str(posts_path),
        "--delay",
        "0",
    ]

    runner.invoke(cli_module.cli, base_args)
    no_retry_result = runner.invoke(cli_module.cli, [*base_args, "--no-retry-failed"])
    assert no_retry_result.exit_code == 0
    assert "Nothing to back up" in no_retry_result.output


def test_backup_respects_limit(tmp_path, monkeypatch):
    talks_path = tmp_path / "talks.yaml"
    posts_path = tmp_path / "posts"
    write_talks(talks_path)
    write_posts(posts_path)
    archive_root = tmp_path / "archive"
    calls = []

    def counting_download(url, kind, root):
        calls.append(url)
        return _fake_download_success(url, kind, root)

    monkeypatch.setattr(cli_module, "download_candidate", counting_download)
    monkeypatch.setattr(cli_module, "ffmpeg_available", lambda: True)
    runner = CliRunner()
    result = runner.invoke(
        cli_module.cli,
        [
            "backup",
            "--archive-root",
            str(archive_root),
            "--talks-path",
            str(talks_path),
            "--posts-path",
            str(posts_path),
            "--delay",
            "0",
            "--limit",
            "1",
        ],
    )

    assert result.exit_code == 0
    assert len(calls) == 1


def test_backup_warns_when_ffmpeg_missing(tmp_path, monkeypatch):
    talks_path = tmp_path / "talks.yaml"
    posts_path = tmp_path / "posts"
    write_talks(talks_path)
    write_posts(posts_path)
    archive_root = tmp_path / "archive"
    monkeypatch.setattr(cli_module, "download_candidate", _fake_download_success)
    monkeypatch.setattr(cli_module, "ffmpeg_available", lambda: False)

    runner = CliRunner()
    result = runner.invoke(
        cli_module.cli,
        [
            "backup",
            "--archive-root",
            str(archive_root),
            "--talks-path",
            str(talks_path),
            "--posts-path",
            str(posts_path),
            "--delay",
            "0",
        ],
    )

    assert "ffmpeg was not found" in result.output


def test_verify_reports_no_media_when_manifest_empty(tmp_path):
    archive_root = tmp_path / "archive"
    archive_root.mkdir()

    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["verify", "--archive-root", str(archive_root)])

    assert result.exit_code == 0
    assert "No successfully archived media" in result.output


def test_verify_passes_for_intact_file(tmp_path):
    archive_root = tmp_path / "archive"
    archive_root.mkdir()
    media_path = archive_root / "direct" / "file.bin"
    media_path.parent.mkdir(parents=True)
    media_path.write_bytes(b"hello world")

    entry = manifest_mod.ManifestEntry(
        source_url="https://example.com/clip.mp4",
        kind="direct",
        occurrences=[],
        status=manifest_mod.STATUS_SUCCESS,
        output_filename="direct/file.bin",
        size_bytes=media_path.stat().st_size,
        sha256=manifest_mod.sha256_file(media_path),
        created_at=manifest_mod.current_timestamp(),
        updated_at=manifest_mod.current_timestamp(),
    )
    manifest = manifest_mod.Manifest(entries={entry.source_url: entry})
    manifest_mod.write_manifest(archive_root, manifest)

    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["verify", "--archive-root", str(archive_root)])

    assert result.exit_code == 0
    assert "Verified 1 file(s); 0 missing; 0 mismatched." in result.output


def test_verify_reports_missing_file(tmp_path):
    archive_root = tmp_path / "archive"
    archive_root.mkdir()

    entry = manifest_mod.ManifestEntry(
        source_url="https://example.com/clip.mp4",
        kind="direct",
        occurrences=[],
        status=manifest_mod.STATUS_SUCCESS,
        output_filename="direct/missing.bin",
        size_bytes=5,
        sha256="deadbeef",
        created_at=manifest_mod.current_timestamp(),
        updated_at=manifest_mod.current_timestamp(),
    )
    manifest = manifest_mod.Manifest(entries={entry.source_url: entry})
    manifest_mod.write_manifest(archive_root, manifest)

    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["verify", "--archive-root", str(archive_root)])

    assert result.exit_code == 1
    assert "MISSING" in result.output


def test_verify_reports_mismatched_checksum(tmp_path):
    archive_root = tmp_path / "archive"
    archive_root.mkdir()
    media_path = archive_root / "direct" / "file.bin"
    media_path.parent.mkdir(parents=True)
    media_path.write_bytes(b"hello world")

    entry = manifest_mod.ManifestEntry(
        source_url="https://example.com/clip.mp4",
        kind="direct",
        occurrences=[],
        status=manifest_mod.STATUS_SUCCESS,
        output_filename="direct/file.bin",
        size_bytes=999,
        sha256="not-the-real-hash",
        created_at=manifest_mod.current_timestamp(),
        updated_at=manifest_mod.current_timestamp(),
    )
    manifest = manifest_mod.Manifest(entries={entry.source_url: entry})
    manifest_mod.write_manifest(archive_root, manifest)

    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["verify", "--archive-root", str(archive_root)])

    assert result.exit_code == 1
    assert "MISMATCH" in result.output


def test_verify_requires_archive_root():
    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["verify"])
    assert result.exit_code == 1
    assert "An archive root is required" in result.output


def test_verify_skips_entries_without_output_filename(tmp_path):
    archive_root = tmp_path / "archive"
    archive_root.mkdir()
    entry = manifest_mod.ManifestEntry(
        source_url="https://example.com/clip.mp4",
        kind="direct",
        occurrences=[],
        status=manifest_mod.STATUS_SUCCESS,
        output_filename=None,
    )
    manifest = manifest_mod.Manifest(entries={entry.source_url: entry})
    manifest_mod.write_manifest(archive_root, manifest)

    runner = CliRunner()
    result = runner.invoke(cli_module.cli, ["verify", "--archive-root", str(archive_root)])

    assert result.exit_code == 0
    assert "Verified 0 file(s); 0 missing; 0 mismatched." in result.output


def _raise_download_error(url, kind, archive_root):
    raise downloader.DownloadError("ffmpeg is required but missing")


def test_backup_handles_download_error_raised_directly(tmp_path, monkeypatch):
    talks_path = tmp_path / "talks.yaml"
    posts_path = tmp_path / "posts"
    write_talks(talks_path)
    write_posts(posts_path)
    archive_root = tmp_path / "archive"
    monkeypatch.setattr(cli_module, "download_candidate", _raise_download_error)
    monkeypatch.setattr(cli_module, "ffmpeg_available", lambda: True)

    runner = CliRunner()
    result = runner.invoke(
        cli_module.cli,
        [
            "backup",
            "--archive-root",
            str(archive_root),
            "--talks-path",
            str(talks_path),
            "--posts-path",
            str(posts_path),
            "--delay",
            "0",
        ],
    )

    assert result.exit_code == 1
    manifest = manifest_mod.load_manifest(archive_root)
    assert all(entry.status == manifest_mod.STATUS_FAILED for entry in manifest.entries.values())
    assert all("ffmpeg is required" in (entry.error or "") for entry in manifest.entries.values())
