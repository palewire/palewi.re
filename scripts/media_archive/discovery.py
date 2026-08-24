"""Discover playable audio/video sources in talks and blog posts.

This module never downloads or fetches anything over the network. It only
parses already-loaded content (:mod:`coltrane.content_loaders`) and applies
conservative pattern matching to decide whether a URL is a playable media
source worth preserving.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlsplit

from bs4 import BeautifulSoup

from coltrane.content_loaders import MarkdownPost, Talk

# ---------------------------------------------------------------------------
# Known media file extensions and hosts
# ---------------------------------------------------------------------------

# File extensions that identify a direct, playable media file regardless of
# the host that serves it (self-hosted clips, S3 buckets, CDNs, and so on).
DIRECT_MEDIA_EXTENSIONS = frozenset(
    {
        ".mp4",
        ".m4v",
        ".mov",
        ".webm",
        ".mkv",
        ".avi",
        ".mp3",
        ".m4a",
        ".wav",
        ".ogg",
        ".oga",
        ".flac",
        ".aac",
        ".wma",
    }
)

_VIMEO_WATCH_RE = re.compile(r"^https?://(?:www\.)?vimeo\.com/(\d+)")
_VIMEO_PLAYER_RE = re.compile(r"^https?://player\.vimeo\.com/video/(\d+)")
_YOUTUBE_WATCH_RE = re.compile(
    r"^https?://(?:www\.|m\.)?(?:youtube\.com|youtube-nocookie\.com)/watch\?(?:.*&)?v=([\w-]{6,})"
)
_YOUTUBE_EMBED_RE = re.compile(r"^https?://(?:www\.)?(?:youtube\.com|youtube-nocookie\.com)/embed/([\w-]{6,})")
_YOUTUBE_SHORT_RE = re.compile(r"^https?://youtu\.be/([\w-]{6,})")
_SOUNDCLOUD_TRACK_RE = re.compile(r"^https?://(?:www\.)?soundcloud\.com/[^/?#]+/[^/?#]+")
_SOUNDCLOUD_PLAYER_RE = re.compile(r"^https?://w\.soundcloud\.com/player/")

KIND_DIRECT = "direct"
KIND_YOUTUBE = "youtube"
KIND_VIMEO = "vimeo"
KIND_SOUNDCLOUD = "soundcloud"
KIND_UNKNOWN = "unknown"

# The site's canonical origin, used to resolve site-relative media links
# (e.g. ``<a href="/media/mp3/clip.mp3">``) into absolute, downloadable URLs.
SITE_BASE_URL = "https://palewi.re"


# ---------------------------------------------------------------------------
# Typed results
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MediaOccurrence:
    """One place a media URL was found."""

    origin_type: str  # "talk" | "post"
    origin_id: str  # talk identifier or post slug
    location: str  # e.g. "video_url", "video", "audio>source", "iframe", "a"
    raw_url: str  # the exact string found in the source content


@dataclass(frozen=True)
class MediaCandidate:
    """A deduplicated, playable media URL and every place it was found."""

    url: str
    kind: str
    occurrences: tuple[MediaOccurrence, ...]


# ---------------------------------------------------------------------------
# URL classification
# ---------------------------------------------------------------------------


def normalize_url(url: str) -> str:
    """Resolve protocol-relative and site-relative URLs; strip surrounding whitespace.

    Protocol-relative URLs (``//host/path``) are given an ``https:`` scheme.
    Site-relative paths (``/media/...``) are resolved against
    :data:`SITE_BASE_URL` so they become downloadable absolute URLs, since
    they only ever appear in this site's own content referring to media it
    hosts itself.
    """
    stripped = url.strip()
    if stripped.startswith("//"):
        return f"https:{stripped}"
    if stripped.startswith("/"):
        return urljoin(f"{SITE_BASE_URL}/", stripped.lstrip("/"))
    return stripped


def _extension(url: str) -> str:
    """Return the lowercase file extension of a URL's path, ignoring the query string."""
    path = urlsplit(url).path
    if "." not in path:
        return ""
    return "." + path.rsplit(".", 1)[-1].lower()


def classify_media_url(url: str) -> str | None:
    """Classify a direct link or media-element ``src`` as a known playable kind.

    Returns ``None`` when the URL does not look like playable media, such as
    an ordinary webpage, an image, a social profile link, or a hosted
    interactive.
    """
    normalized = normalize_url(url)
    if _extension(normalized) in DIRECT_MEDIA_EXTENSIONS:
        return KIND_DIRECT
    if (
        _YOUTUBE_WATCH_RE.match(normalized)
        or _YOUTUBE_EMBED_RE.match(normalized)
        or _YOUTUBE_SHORT_RE.match(normalized)
    ):
        return KIND_YOUTUBE
    if _VIMEO_WATCH_RE.match(normalized) or _VIMEO_PLAYER_RE.match(normalized):
        return KIND_VIMEO
    if _SOUNDCLOUD_TRACK_RE.match(normalized):
        return KIND_SOUNDCLOUD
    return None


def classify_iframe_url(url: str) -> tuple[str, str] | None:
    """Classify an ``<iframe src>`` from a known media-host embed.

    Returns ``(kind, canonical_url)`` for a recognized embed, resolving the
    embed's player URL back to the canonical page for the underlying media.
    Returns ``None`` for generic iframes (Google Slides, hosted interactives,
    maps, and so on), which are never treated as media candidates.
    """
    normalized = normalize_url(url)
    vimeo_match = _VIMEO_PLAYER_RE.match(normalized)
    if vimeo_match:
        return KIND_VIMEO, f"https://vimeo.com/{vimeo_match.group(1)}"
    youtube_match = _YOUTUBE_EMBED_RE.match(normalized)
    if youtube_match:
        return KIND_YOUTUBE, f"https://www.youtube.com/watch?v={youtube_match.group(1)}"
    if _SOUNDCLOUD_PLAYER_RE.match(normalized):
        query = parse_qs(urlsplit(normalized).query)
        track_urls = query.get("url")
        if track_urls and track_urls[0]:
            return KIND_SOUNDCLOUD, unquote(track_urls[0])
    return None


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def _talk_origin_id(talk: Talk) -> str:
    """Build a stable, human-readable identifier for a talk without a slug."""
    return f"{talk.date.isoformat()} {talk.title}"


def discover_talk_occurrence(talk: Talk) -> tuple[str, str, MediaOccurrence] | None:
    """Return the ``(url, kind, occurrence)`` for a talk's video, if any.

    Every non-empty ``video_url`` is preserved because the field's meaning
    already guarantees it is a video link curated by the author. Unrecognized
    hosts still get a candidate (``kind="unknown"``) so yt-dlp's own
    site-detection can attempt the download.
    """
    if not talk.video_url:
        return None
    kind = classify_media_url(talk.video_url) or KIND_UNKNOWN
    occurrence = MediaOccurrence(
        origin_type="talk",
        origin_id=_talk_origin_id(talk),
        location="video_url",
        raw_url=talk.video_url,
    )
    return talk.video_url, kind, occurrence


def _attribute(tag: Any, name: str) -> str | None:
    """Return a tag attribute as a plain string, or ``None`` if absent."""
    value = tag.get(name)
    if value is None:
        return None
    if isinstance(value, list):
        return "".join(value)
    return str(value)


def discover_post_occurrences(post: MarkdownPost) -> list[tuple[str, str, MediaOccurrence]]:
    """Return every ``(url, kind, occurrence)`` found in one post's body."""
    results: list[tuple[str, str, MediaOccurrence]] = []
    soup = BeautifulSoup(post.body_markup, "html.parser")

    for tag_name in ("video", "audio"):
        for media_tag in soup.find_all(tag_name):
            src = _attribute(media_tag, "src")
            if src:
                results.append(
                    (src, classify_media_url(src) or KIND_DIRECT, MediaOccurrence("post", post.slug, tag_name, src))
                )
            for source_tag in media_tag.find_all("source"):
                source_src = _attribute(source_tag, "src")
                if source_src:
                    results.append(
                        (
                            source_src,
                            classify_media_url(source_src) or KIND_DIRECT,
                            MediaOccurrence("post", post.slug, f"{tag_name}>source", source_src),
                        )
                    )

    for iframe_tag in soup.find_all("iframe"):
        src = _attribute(iframe_tag, "src")
        if not src:
            continue
        classified = classify_iframe_url(src)
        if classified is None:
            continue
        kind, canonical_url = classified
        results.append((canonical_url, kind, MediaOccurrence("post", post.slug, "iframe", src)))

    for anchor_tag in soup.find_all("a"):
        href = _attribute(anchor_tag, "href")
        if not href:
            continue
        kind = classify_media_url(href)
        if kind is None:
            continue
        results.append((href, kind, MediaOccurrence("post", post.slug, "a", href)))

    return results


def discover_candidates(talks: Sequence[Talk], posts: Sequence[MarkdownPost]) -> list[MediaCandidate]:
    """Discover every playable media URL across talks and posts, deduplicated.

    Identical URLs are merged into a single :class:`MediaCandidate`, but every
    occurrence (talk or post that referenced it) is retained. Discovery order
    follows the order talks and posts are supplied in.
    """
    order: list[str] = []
    kinds: dict[str, str] = {}
    occurrences: dict[str, list[MediaOccurrence]] = {}

    def record(url: str, kind: str, occurrence: MediaOccurrence) -> None:
        normalized = normalize_url(url)
        if normalized not in occurrences:
            order.append(normalized)
            kinds[normalized] = kind
            occurrences[normalized] = []
        occurrences[normalized].append(occurrence)

    for talk in talks:
        found = discover_talk_occurrence(talk)
        if found is not None:
            record(*found)

    for post in posts:
        for url, kind, occurrence in discover_post_occurrences(post):
            record(url, kind, occurrence)

    return [MediaCandidate(url=url, kind=kinds[url], occurrences=tuple(occurrences[url])) for url in order]
