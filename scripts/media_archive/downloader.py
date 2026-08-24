"""Download media candidates with yt-dlp as the primary extractor.

This module never bypasses DRM, private access, login walls, or other
publisher controls; it only invokes yt-dlp's standard public extraction
path. Direct media files (plain ``.mp4``/``.mp3`` links, etc.) are handled by
yt-dlp's generic extractor, so every candidate flows through the same code
path regardless of host.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from scripts.media_archive.discovery import KIND_DIRECT

# yt-dlp needs ffmpeg to merge separately downloaded video and audio streams,
# which is common for YouTube and Vimeo. Direct files and most SoundCloud
# tracks are single streams and never require it, so we only check when a
# candidate's kind is likely to need merging.
KINDS_REQUIRING_FFMPEG = frozenset({"youtube", "vimeo", "unknown"})

_UNSAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


class DownloadError(RuntimeError):
    """Raised when a download cannot proceed (e.g. missing ffmpeg)."""


class SupportsExtractInfo(Protocol):
    """The subset of yt-dlp's ``YoutubeDL`` interface this module relies on."""

    def __enter__(self) -> SupportsExtractInfo: ...

    def __exit__(self, *exc_info: object) -> None: ...

    def extract_info(self, url: str, download: bool = True) -> dict[str, Any]: ...


def ffmpeg_available() -> bool:
    """Return whether an ``ffmpeg`` binary is on ``PATH``."""
    return shutil.which("ffmpeg") is not None


def require_ffmpeg(kind: str) -> None:
    """Raise :class:`DownloadError` if a kind needs ffmpeg and it is missing."""
    if kind in KINDS_REQUIRING_FFMPEG and not ffmpeg_available():
        raise DownloadError(
            "ffmpeg is required to merge the separate audio and video streams "
            f"yt-dlp downloads for '{kind}' sources. Install ffmpeg and retry."
        )


def _safe_dirname(kind: str) -> str:
    """Return a filesystem-safe subdirectory name for a candidate kind."""
    cleaned = _UNSAFE_FILENAME_RE.sub("-", kind).strip("-")
    return cleaned or "other"


def default_ydl_factory(options: dict[str, Any]) -> SupportsExtractInfo:
    """Build the real yt-dlp client. Imported lazily so tests never need it installed at import time."""
    import yt_dlp

    return yt_dlp.YoutubeDL(options)


@dataclass
class DownloadOutcome:
    """The result of attempting to download a single media candidate."""

    status: str  # "success" | "failed"
    extractor: str | None = None
    media_id: str | None = None
    output_filename: str | None = None
    size_bytes: int | None = None
    info_json_path: str | None = None
    error: str | None = None


def _resolve_output_path(ydl: SupportsExtractInfo, info: dict[str, Any], output_dir: Path) -> Path | None:
    """Find the file yt-dlp actually wrote, which may differ from the template after post-processing."""
    requested_downloads = info.get("requested_downloads")
    if isinstance(requested_downloads, list) and requested_downloads:
        filepath = requested_downloads[0].get("filepath") or requested_downloads[0].get("_filename")
        if filepath:
            return Path(filepath)
    filepath = info.get("filepath") or info.get("_filename")
    if filepath:
        return Path(filepath)
    prepare_filename = getattr(ydl, "prepare_filename", None)
    if callable(prepare_filename):
        try:
            return Path(prepare_filename(info))
        except Exception:  # pragma: no cover - defensive fallback only
            return None
    return None


def download_candidate(
    url: str,
    kind: str,
    archive_root: Path,
    *,
    ydl_factory: Any = default_ydl_factory,
) -> DownloadOutcome:
    """Download one media candidate with yt-dlp and report the outcome.

    Never raises for ordinary extraction/download failures — those are
    captured explicitly in the returned :class:`DownloadOutcome` so callers
    can record them in the manifest instead of losing them. Only a missing
    ffmpeg dependency raises :class:`DownloadError`, since that is a
    fixable environment problem rather than a per-item failure.
    """
    require_ffmpeg(kind)
    output_dir = archive_root / _safe_dirname(kind)
    output_dir.mkdir(parents=True, exist_ok=True)

    options: dict[str, Any] = {
        "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
        "writeinfojson": True,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
    }
    if kind == KIND_DIRECT:
        # Never let the generic extractor treat a direct file link as a
        # webpage to crawl for other links.
        options["force_generic_extractor"] = True

    try:
        with ydl_factory(options) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as error:  # yt-dlp raises many different error types
        return DownloadOutcome(status="failed", error=str(error))

    if not isinstance(info, dict):
        return DownloadOutcome(status="failed", error="yt-dlp returned no metadata for this URL")

    output_path = _resolve_output_path(ydl, info, output_dir)
    if output_path is None or not output_path.exists():
        return DownloadOutcome(status="failed", error="yt-dlp reported success but the output file is missing")

    info_json_path = output_path.with_suffix(".info.json")

    return DownloadOutcome(
        status="success",
        extractor=info.get("extractor_key") or info.get("extractor"),
        media_id=info.get("id"),
        output_filename=str(output_path.relative_to(archive_root)),
        size_bytes=output_path.stat().st_size,
        info_json_path=str(info_json_path.relative_to(archive_root)) if info_json_path.exists() else None,
    )
