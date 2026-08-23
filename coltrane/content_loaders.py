"""
YAML content loaders for bio-page data, slogans, and bots.

Each loader reads a YAML file, validates the structure and field types, and
returns a list of typed dataclass instances ready for use in views.

Adding or updating content
--------------------------
Edit the appropriate file under ``coltrane/content/``:

* ``awards.yaml``  – Honors listed on the bio page.
  Required fields: ``title`` (str).
  Optional fields: ``url`` (str), ``year`` (int).
  Ordering: ``-year``, then ``title`` (alphabetical).

* ``clips.yaml``   – Work items listed on the /work/ page.
  Required fields: ``title`` (str), ``type`` (one of ``app``,
  ``lesson-plan``, ``story``, ``software``), ``date`` (YYYY-MM-DD),
  ``url`` (str, unique).
  Ordering: ``-date``.

* ``talks.yaml``   – Talks listed on the /talks/ page.
  Required fields: ``title`` (str), ``venue`` (str), ``location`` (str),
  ``date`` (YYYY-MM-DD).
  Optional fields: ``video_url`` (str), ``slides_url`` (str).
  Ordering: ``-date``.

* ``docs.yaml``    – Documentation listed on the /docs/ page.
  Required fields: ``title`` (str), ``type`` (one of
  ``lesson-plan``, ``software``), ``url`` (str, unique).
  Optional fields: ``description`` (str).
  Ordering: ``type``, then ``title`` (alphabetical).

* ``slogans.yaml`` – Short phrases that appear in the site header.
  Required fields: ``title`` (str, non-empty).
  Ordering: alphabetical by title.

* ``bots.yaml``    – Automated accounts listed on /bots/.
  Required fields: ``title`` (str), ``mastodon_url`` (str).
  Optional fields: ``twitter_url`` (str, default ``""``).
  Constraints: ``mastodon_url`` must be unique; non-empty ``twitter_url``
  values must be unique across the list.
  Ordering: preserved from file (explicit list order).

After editing, run ``make check`` to validate.
"""

from __future__ import annotations

import datetime
import random
from dataclasses import dataclass
from pathlib import Path

import yaml

CONTENT_PATH = Path(__file__).resolve().parent / "content"

CLIP_TYPES = frozenset({"app", "lesson-plan", "story", "software"})
DOC_TYPES = frozenset({"lesson-plan", "software"})


# ---------------------------------------------------------------------------
# Typed content objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Award:
    title: str
    url: str = ""
    year: int | None = None


@dataclass(frozen=True)
class Clip:
    title: str
    type: str
    date: datetime.date
    url: str


@dataclass(frozen=True)
class Talk:
    title: str
    venue: str
    location: str
    date: datetime.date
    video_url: str = ""
    slides_url: str = ""


@dataclass(frozen=True)
class Doc:
    title: str
    type: str
    url: str
    description: str = ""


@dataclass(frozen=True)
class Slogan:
    title: str


@dataclass(frozen=True)
class Bot:
    title: str
    mastodon_url: str
    twitter_url: str = ""


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


class ContentError(ValueError):
    """Raised when a YAML content file fails validation."""


def _require_str(record: dict, field_name: str, path: str) -> str:
    """Return a non-empty string field or raise ContentError."""
    value = record.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ContentError(f"{path}: record {record!r} must have a non-empty string field '{field_name}'")
    return value


def _require_date(record: dict, field_name: str, path: str) -> datetime.date:
    """Return a datetime.date field (accept date or YYYY-MM-DD string)."""
    value = record.get(field_name)
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        try:
            return datetime.date.fromisoformat(value)
        except ValueError:
            pass
    raise ContentError(f"{path}: record {record!r} field '{field_name}' must be a date (YYYY-MM-DD), got {value!r}")


def _optional_str(record: dict, field_name: str, path: str) -> str:
    """Return an optional string field, defaulting to ''."""
    value = record.get(field_name, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ContentError(
            f"{path}: record {record!r} field '{field_name}' must be a string, got {type(value).__name__}"
        )
    return value


# ---------------------------------------------------------------------------
# Public loaders
# ---------------------------------------------------------------------------


def load_awards(path: Path | None = None) -> list[Award]:
    """Load and validate awards from YAML, return sorted list."""
    if path is None:
        path = CONTENT_PATH / "awards.yaml"
    label = str(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ContentError(f"{label}: top-level structure must be a mapping")
    items = raw.get("awards", [])
    if not isinstance(items, list):
        raise ContentError(f"{label}: 'awards' must be a list")
    awards: list[Award] = []
    for record in items:
        if not isinstance(record, dict):
            raise ContentError(f"{label}: each award must be a mapping, got {record!r}")
        title = _require_str(record, "title", label)
        url = _optional_str(record, "url", label)
        year_raw = record.get("year")
        if year_raw is not None:
            if not isinstance(year_raw, int):
                raise ContentError(f"{label}: award '{title}' field 'year' must be an integer")
            year: int | None = year_raw
        else:
            year = None
        awards.append(Award(title=title, url=url, year=year))
    # Sort: descending year (None last), then title
    awards.sort(key=lambda a: (-(a.year or 0), a.title))
    return awards


def load_clips(path: Path | None = None) -> list[Clip]:
    """Load and validate clips from YAML, return sorted list."""
    if path is None:
        path = CONTENT_PATH / "clips.yaml"
    label = str(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ContentError(f"{label}: top-level structure must be a mapping")
    items = raw.get("clips", [])
    if not isinstance(items, list):
        raise ContentError(f"{label}: 'clips' must be a list")
    seen_urls: set[str] = set()
    clips: list[Clip] = []
    for record in items:
        if not isinstance(record, dict):
            raise ContentError(f"{label}: each clip must be a mapping, got {record!r}")
        title = _require_str(record, "title", label)
        clip_type = _require_str(record, "type", label)
        if clip_type not in CLIP_TYPES:
            raise ContentError(f"{label}: clip '{title}' type '{clip_type}' must be one of {sorted(CLIP_TYPES)}")
        date = _require_date(record, "date", label)
        url = _require_str(record, "url", label)
        if url in seen_urls:
            raise ContentError(f"{label}: duplicate clip URL '{url}'")
        seen_urls.add(url)
        clips.append(Clip(title=title, type=clip_type, date=date, url=url))
    clips.sort(key=lambda c: c.date, reverse=True)
    return clips


def load_talks(path: Path | None = None) -> list[Talk]:
    """Load and validate talks from YAML, return sorted list."""
    if path is None:
        path = CONTENT_PATH / "talks.yaml"
    label = str(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ContentError(f"{label}: top-level structure must be a mapping")
    items = raw.get("talks", [])
    if not isinstance(items, list):
        raise ContentError(f"{label}: 'talks' must be a list")
    talks: list[Talk] = []
    for record in items:
        if not isinstance(record, dict):
            raise ContentError(f"{label}: each talk must be a mapping, got {record!r}")
        title = _require_str(record, "title", label)
        venue = _require_str(record, "venue", label)
        location = _require_str(record, "location", label)
        date = _require_date(record, "date", label)
        video_url = _optional_str(record, "video_url", label)
        slides_url = _optional_str(record, "slides_url", label)
        talks.append(
            Talk(
                title=title,
                venue=venue,
                location=location,
                date=date,
                video_url=video_url,
                slides_url=slides_url,
            )
        )
    talks.sort(key=lambda t: t.date, reverse=True)
    return talks


def load_docs(path: Path | None = None) -> list[Doc]:
    """Load and validate docs from YAML, return sorted list."""
    if path is None:
        path = CONTENT_PATH / "docs.yaml"
    label = str(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ContentError(f"{label}: top-level structure must be a mapping")
    items = raw.get("docs", [])
    if not isinstance(items, list):
        raise ContentError(f"{label}: 'docs' must be a list")
    seen_urls: set[str] = set()
    docs: list[Doc] = []
    for record in items:
        if not isinstance(record, dict):
            raise ContentError(f"{label}: each doc must be a mapping, got {record!r}")
        title = _require_str(record, "title", label)
        doc_type = _require_str(record, "type", label)
        if doc_type not in DOC_TYPES:
            raise ContentError(f"{label}: doc '{title}' type '{doc_type}' must be one of {sorted(DOC_TYPES)}")
        url = _require_str(record, "url", label)
        if url in seen_urls:
            raise ContentError(f"{label}: duplicate doc URL '{url}'")
        seen_urls.add(url)
        description = _optional_str(record, "description", label)
        docs.append(Doc(title=title, type=doc_type, url=url, description=description))
    docs.sort(key=lambda d: (d.type, d.title))
    return docs


def load_slogans(path: Path | None = None) -> list[Slogan]:
    """Load and validate slogans from YAML, return alphabetically sorted list."""
    if path is None:
        path = CONTENT_PATH / "slogans.yaml"
    label = str(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ContentError(f"{label}: top-level structure must be a mapping")
    items = raw.get("slogans", [])
    if not isinstance(items, list):
        raise ContentError(f"{label}: 'slogans' must be a list")
    slogans: list[Slogan] = []
    for record in items:
        if not isinstance(record, dict):
            raise ContentError(f"{label}: each slogan must be a mapping, got {record!r}")
        title = _require_str(record, "title", label)
        slogans.append(Slogan(title=title))
    slogans.sort(key=lambda s: s.title)
    return slogans


def random_slogan(path: Path | None = None) -> Slogan | None:
    """Return a single randomly selected slogan, or None if the list is empty."""
    slogans = load_slogans(path)
    return random.choice(slogans) if slogans else None


def load_bots(path: Path | None = None) -> list[Bot]:
    """Load and validate bots from YAML, preserving file order."""
    if path is None:
        path = CONTENT_PATH / "bots.yaml"
    label = str(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ContentError(f"{label}: top-level structure must be a mapping")
    items = raw.get("bots", [])
    if not isinstance(items, list):
        raise ContentError(f"{label}: 'bots' must be a list")
    seen_mastodon: set[str] = set()
    seen_twitter: set[str] = set()
    bots: list[Bot] = []
    for record in items:
        if not isinstance(record, dict):
            raise ContentError(f"{label}: each bot must be a mapping, got {record!r}")
        title = _require_str(record, "title", label)
        mastodon_url = _require_str(record, "mastodon_url", label)
        if not mastodon_url.startswith("http"):
            raise ContentError(f"{label}: bot '{title}' mastodon_url must be a URL, got {mastodon_url!r}")
        if mastodon_url in seen_mastodon:
            raise ContentError(f"{label}: duplicate bot mastodon_url '{mastodon_url}'")
        seen_mastodon.add(mastodon_url)
        twitter_url = _optional_str(record, "twitter_url", label)
        if twitter_url:
            if not twitter_url.startswith("http"):
                raise ContentError(f"{label}: bot '{title}' twitter_url must be a URL, got {twitter_url!r}")
            if twitter_url in seen_twitter:
                raise ContentError(f"{label}: duplicate bot twitter_url '{twitter_url}'")
            seen_twitter.add(twitter_url)
        bots.append(Bot(title=title, mastodon_url=mastodon_url, twitter_url=twitter_url))
    return bots
