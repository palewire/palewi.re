"""Tests for the yt-dlp download wrapper."""

from pathlib import Path

import pytest

from scripts.media_archive import downloader


class FakeYoutubeDL:
    """A minimal stand-in for yt_dlp.YoutubeDL that never touches the network."""

    def __init__(self, options, *, info=None, error=None, write_file=True, write_info_json=False):
        self.options = options
        self._info = info
        self._error = error
        self._write_file = write_file
        self._write_info_json = write_info_json

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def extract_info(self, url, download=True):
        if self._error is not None:
            raise self._error
        if self._write_file and self._info is not None:
            output_path = Path(
                self.options["outtmpl"].replace("%(id)s", self._info["id"]).replace("%(ext)s", self._info["ext"])
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"fake media bytes")
            if self._write_info_json:
                output_path.with_suffix(".info.json").write_text("{}", encoding="utf-8")
        return self._info

    def prepare_filename(self, info):
        return self.options["outtmpl"].replace("%(id)s", info["id"]).replace("%(ext)s", info["ext"])


def make_factory(**kwargs):
    def factory(options):
        return FakeYoutubeDL(options, **kwargs)

    return factory


def test_ffmpeg_available_reflects_shutil_which(monkeypatch):
    monkeypatch.setattr(downloader.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    assert downloader.ffmpeg_available() is True
    monkeypatch.setattr(downloader.shutil, "which", lambda name: None)
    assert downloader.ffmpeg_available() is False


def test_require_ffmpeg_raises_for_kinds_that_need_it(monkeypatch):
    monkeypatch.setattr(downloader, "ffmpeg_available", lambda: False)
    with pytest.raises(downloader.DownloadError, match="ffmpeg"):
        downloader.require_ffmpeg("youtube")
    with pytest.raises(downloader.DownloadError):
        downloader.require_ffmpeg("vimeo")
    with pytest.raises(downloader.DownloadError):
        downloader.require_ffmpeg("unknown")


def test_require_ffmpeg_skips_kinds_that_do_not_need_it(monkeypatch):
    monkeypatch.setattr(downloader, "ffmpeg_available", lambda: False)
    downloader.require_ffmpeg("direct")
    downloader.require_ffmpeg("soundcloud")


def test_require_ffmpeg_passes_when_available(monkeypatch):
    monkeypatch.setattr(downloader, "ffmpeg_available", lambda: True)
    downloader.require_ffmpeg("youtube")


def test_download_candidate_success_direct(tmp_path, monkeypatch):
    monkeypatch.setattr(downloader, "ffmpeg_available", lambda: True)
    factory = make_factory(info={"id": "abc123", "ext": "mp4", "extractor_key": "Generic"})

    outcome = downloader.download_candidate("https://example.com/clip.mp4", "direct", tmp_path, ydl_factory=factory)

    assert outcome.status == "success"
    assert outcome.media_id == "abc123"
    assert outcome.extractor == "Generic"
    assert outcome.output_filename == "direct/abc123.mp4"
    assert outcome.size_bytes == len(b"fake media bytes")
    assert (tmp_path / "direct" / "abc123.mp4").exists()


def test_download_candidate_success_youtube_requires_ffmpeg(tmp_path, monkeypatch):
    monkeypatch.setattr(downloader, "ffmpeg_available", lambda: False)
    factory = make_factory(info={"id": "abc123", "ext": "mp4"})

    with pytest.raises(downloader.DownloadError):
        downloader.download_candidate(
            "https://www.youtube.com/watch?v=abc123", "youtube", tmp_path, ydl_factory=factory
        )


def test_download_candidate_uses_requested_downloads_filepath(tmp_path, monkeypatch):
    monkeypatch.setattr(downloader, "ffmpeg_available", lambda: True)
    output_dir = tmp_path / "youtube"
    output_dir.mkdir(parents=True)
    real_path = output_dir / "abc123.mp4"
    real_path.write_bytes(b"12345")
    info = {
        "id": "abc123",
        "ext": "mp4",
        "extractor_key": "Youtube",
        "requested_downloads": [{"filepath": str(real_path)}],
    }
    factory = make_factory(info=info, write_file=False)

    outcome = downloader.download_candidate(
        "https://www.youtube.com/watch?v=abc123", "youtube", tmp_path, ydl_factory=factory
    )

    assert outcome.status == "success"
    assert outcome.output_filename == "youtube/abc123.mp4"
    assert outcome.size_bytes == 5


def test_download_candidate_records_info_json_when_present(tmp_path, monkeypatch):
    monkeypatch.setattr(downloader, "ffmpeg_available", lambda: True)
    factory = make_factory(info={"id": "abc123", "ext": "mp4", "extractor_key": "Generic"}, write_info_json=True)

    outcome = downloader.download_candidate("https://example.com/clip.mp4", "direct", tmp_path, ydl_factory=factory)

    assert outcome.info_json_path == "direct/abc123.info.json"


def test_download_candidate_failure_from_extractor_exception(tmp_path, monkeypatch):
    monkeypatch.setattr(downloader, "ffmpeg_available", lambda: True)
    factory = make_factory(error=RuntimeError("network unreachable"))

    outcome = downloader.download_candidate("https://example.com/clip.mp4", "direct", tmp_path, ydl_factory=factory)

    assert outcome.status == "failed"
    assert outcome.error is not None
    assert "network unreachable" in outcome.error


def test_download_candidate_failure_when_info_not_dict(tmp_path, monkeypatch):
    monkeypatch.setattr(downloader, "ffmpeg_available", lambda: True)
    factory = make_factory(info=None, write_file=False)

    outcome = downloader.download_candidate("https://example.com/clip.mp4", "direct", tmp_path, ydl_factory=factory)

    assert outcome.status == "failed"
    assert outcome.error is not None
    assert "no metadata" in outcome.error


def test_download_candidate_failure_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(downloader, "ffmpeg_available", lambda: True)
    factory = make_factory(info={"id": "abc123", "ext": "mp4"}, write_file=False)

    outcome = downloader.download_candidate("https://example.com/clip.mp4", "direct", tmp_path, ydl_factory=factory)

    assert outcome.status == "failed"
    assert outcome.error is not None
    assert "output file is missing" in outcome.error


def test_default_ydl_factory_builds_real_client(tmp_path):
    client = downloader.default_ydl_factory({"quiet": True})
    assert hasattr(client, "extract_info")


def test_resolve_output_path_uses_top_level_filepath(tmp_path):
    ydl = FakeYoutubeDL({"outtmpl": str(tmp_path / "%(id)s.%(ext)s")})
    info = {"id": "abc", "ext": "mp4", "filepath": str(tmp_path / "abc.mp4")}
    result = downloader._resolve_output_path(ydl, info, tmp_path)
    assert result == Path(tmp_path / "abc.mp4")


def test_resolve_output_path_falls_back_to_prepare_filename(tmp_path):
    ydl = FakeYoutubeDL({"outtmpl": str(tmp_path / "%(id)s.%(ext)s")})
    info = {"id": "abc", "ext": "mp4"}
    result = downloader._resolve_output_path(ydl, info, tmp_path)
    assert result == Path(tmp_path / "abc.mp4")


def test_resolve_output_path_returns_none_without_prepare_filename(tmp_path):
    class NoPrepare:
        def __enter__(self) -> "NoPrepare":
            return self

        def __exit__(self, *exc_info: object) -> None:
            return None

        def extract_info(self, url: str, download: bool = True) -> dict[str, object]:
            return {}

    info = {"id": "abc", "ext": "mp4"}
    assert downloader._resolve_output_path(NoPrepare(), info, tmp_path) is None
