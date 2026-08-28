"""
YAML and Markdown content loaders for the site's published content.

Each loader reads a YAML file, validates the structure and field types, and
returns a list of typed dataclass instances ready for use in views.

Adding or updating content
--------------------------
Edit the appropriate file under ``coltrane/content/``:

* ``awards.yaml``  – Honors listed on the bio page.
  Required fields: ``title`` (str).
  Optional fields: ``url`` (str), ``year`` (int).
  Ordering: ``-year``, then ``title`` (alphabetical).

* ``apps.yaml``    – Standalone apps and services listed on the /apps/ page.
  Required fields: ``title`` (str), ``type`` (one of ``archiving``, ``bot``,
  ``database``, ``personal``), ``url`` (HTTP(S) URL, unique).
  Optional fields: ``description`` (str).
  Ordering: preserved from file (explicit list order).

* ``clips.yaml``   – Published work records routed by type.
  Required fields: ``title`` (str), ``type`` (one of ``app``,
  ``lesson-plan``, ``service``, ``story``, ``software``), ``date`` (YYYY-MM-DD),
  ``url`` (str, unique).
  Optional fields: ``archive_url`` (Wayback snapshot URL),
  ``archive_exemption`` (reason a snapshot cannot be created), ``link_url``
  (alternate HTTP(S) destination when the original is no longer served),
  ``catalog_title`` (matching catalog entry when titles differ).
  Ordering: ``-date``.

* ``code.yaml``    – Open-source projects grouped and alphabetized on /code/.
  Required fields: ``title`` (str), ``type`` (one of ``data``, ``python``,
  ``javascript``, ``other``, ``inactive``), ``url`` (HTTP(S) URL, unique).
  Optional fields: ``description`` (str).

* ``talks.yaml``   – Talks listed on the /talks/ page and, when a ``slug`` is
  supplied, published at /talks/<slug>/.
  Required fields: ``title`` (str), ``venue`` (str), ``location`` (str),
  ``date`` (YYYY-MM-DD).
  Optional fields: ``slug`` (unique URL slug), ``short_title`` (str),
  ``video_url`` (str),
  ``local_video_url`` (str), ``slides_url`` (str), ``deck_url`` (str), ``pdf_url`` (str),
  ``notes_url`` (str), ``notes_text_url`` (str), ``transcript_url`` (str),
  ``transcript_text_url`` (str), ``captions_url`` (str),
  ``poster_url`` (str), ``original_slides_url`` (str), and
  ``original_video_url`` (str).
  Ordering: ``-date``.

* ``docs.yaml``    – Software listed on /code/ and lessons listed on /guides/.
  Required fields: ``title`` (str), ``type`` (one of
  ``lesson-plan``, ``software``), ``url`` (str, unique).
  Optional fields: ``description`` (str), ``repository_url`` (HTTP(S) URL,
  unique when non-empty).
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
import re
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import yaml
from django.utils import timezone

CONTENT_PATH = Path(__file__).resolve().parent / "content"

CLIP_TYPES = frozenset({"app", "lesson-plan", "service", "story", "software"})
APP_TYPES = frozenset({"archiving", "bot", "database", "personal"})
APP_TYPE_LABELS = {
    "archiving": "Archiving",
    "database": "Databases",
    "bot": "Social media bots",
    "personal": "Personal websites",
}
CODE_TYPES = frozenset({"data", "inactive", "javascript", "other", "python"})
CODE_TYPE_LABELS = {
    "python": "Python",
    "javascript": "JavaScript",
    "data": "Data",
    "other": "Other",
    "inactive": "Inactive",
}
DOC_TYPES = frozenset({"lesson-plan", "software"})
LOS_ANGELES = ZoneInfo("America/Los_Angeles")
POST_FRONT_MATTER_FIELDS = frozenset({"title", "slug", "published_at", "repr_image", "wordpress_id"})


# ---------------------------------------------------------------------------
# Typed content objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Award:
    title: str
    url: str = ""
    year: int | None = None


@dataclass(frozen=True)
class App:
    title: str
    type: str
    url: str
    description: str = ""


@dataclass(frozen=True)
class AppCategory:
    title: str
    object_list: list[App]


@dataclass(frozen=True)
class CodeProject:
    title: str
    type: str
    url: str
    description: str = ""


@dataclass(frozen=True)
class CodeCategory:
    title: str
    object_list: list[CodeProject]


@dataclass(frozen=True)
class Clip:
    title: str
    type: str
    date: datetime.date
    url: str
    archive_url: str = ""
    archive_exemption: str = ""
    catalog_title: str = ""
    link_url: str = ""

    @property
    def display_url(self) -> str:
        return self.link_url or self.url

    @property
    def is_linkable(self) -> bool:
        parsed = urlparse(self.display_url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


@dataclass(frozen=True)
class Talk:
    title: str
    venue: str
    location: str
    date: datetime.date
    video_url: str = ""
    local_video_url: str = ""
    slides_url: str = ""
    slug: str = ""
    short_title: str = ""
    deck_url: str = ""
    pdf_url: str = ""
    notes_url: str = ""
    notes_template: str = ""
    notes_text_url: str = ""
    transcript_url: str = ""
    transcript_template: str = ""
    transcript_text_url: str = ""
    captions_url: str = ""
    poster_url: str = ""
    original_slides_url: str = ""
    original_video_url: str = ""

    def get_absolute_url(self) -> str:
        """Return the permanent public page for talks that have one."""
        return f"/talks/{self.slug}/" if self.slug else "/talks/"

    @property
    def display_subtitle(self) -> str:
        """Return the full title without a repeated short title."""
        if self.short_title:
            prefix = f"{self.short_title}:"
            if self.title.startswith(prefix):
                return self.title.removeprefix(prefix).lstrip()
        return self.title


@dataclass(frozen=True)
class Doc:
    title: str
    type: str
    url: str
    description: str = ""
    repository_url: str = ""


@dataclass(frozen=True)
class Slogan:
    title: str


@dataclass(frozen=True)
class Bot:
    title: str
    mastodon_url: str
    twitter_url: str = ""


@dataclass(frozen=True)
class MarkdownPost:
    """A public blog post loaded from validated Markdown content."""

    title: str
    slug: str
    published_at: datetime.datetime
    body_markup: str
    repr_image: str = ""
    wordpress_id: int | None = None

    def __str__(self) -> str:
        """Return the title used by the existing post list template."""
        return self.title

    @property
    def pub_date(self) -> datetime.datetime:
        """Expose the legacy template and sitemap publication field."""
        return self.published_at

    @cached_property
    def body_html(self) -> str:
        """Apply the existing legacy code-block renderer to stored raw HTML."""
        from coltrane.utils.pygmenter import pygmenter

        return pygmenter(self.body_markup)

    def get_absolute_url(self) -> str:
        """Return the legacy publication-date permalink."""
        return f"/posts/{self.published_at:%Y}/{self.published_at:%m}/{self.published_at:%d}/{self.slug}/"

    url = property(get_absolute_url)


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


def _optional_http_url(record: dict, field_name: str, path: str, title: str) -> str:
    """Return an optional HTTP(S) URL with doc-specific error context."""
    value = record.get(field_name, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ContentError(f"{path}: doc '{title}' field '{field_name}' must be a string, got {type(value).__name__}")
    parsed = urlparse(value)
    if value and (parsed.scheme not in {"http", "https"} or not parsed.netloc or any(char.isspace() for char in value)):
        raise ContentError(f"{path}: doc '{title}' {field_name} must be an HTTP(S) URL, got {value!r}")
    return value


def _require_http_url(record: dict, field_name: str, path: str) -> str:
    """Return a required HTTP(S) URL or raise ContentError."""
    value = _require_str(record, field_name, path)
    return _validate_http_url(value, field_name, path)


def _validate_http_url(value: str, field_name: str, path: str) -> str:
    """Return an HTTP(S) URL or raise a field-specific ContentError."""
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or any(char.isspace() for char in value):
        raise ContentError(f"{path}: field '{field_name}' must be an HTTP(S) URL, got {value!r}")
    return value


def _require_los_angeles_datetime(record: dict, field_name: str, path: str) -> datetime.datetime:
    """Return an ISO datetime expressed in the Los Angeles timezone."""
    value = _require_str(record, field_name, path)
    return parse_los_angeles_datetime(value, field_name, path)


def parse_los_angeles_datetime(value: str, field_name: str, path: str) -> datetime.datetime:
    """Validate an ISO datetime expressed in the Los Angeles timezone."""
    try:
        parsed = datetime.datetime.fromisoformat(value)
    except ValueError as error:
        raise ContentError(f"{path}: field '{field_name}' must be an ISO 8601 datetime") from error
    if not timezone.is_aware(parsed):
        raise ContentError(f"{path}: field '{field_name}' must include a timezone offset")
    los_angeles_time = parsed.astimezone(LOS_ANGELES)
    # This round trip rejects invalid spring-forward wall times while retaining
    # the supplied offset that distinguishes either fall-back occurrence.
    if (
        parsed.replace(tzinfo=None) != los_angeles_time.replace(tzinfo=None)
        or parsed.utcoffset() != los_angeles_time.utcoffset()
    ):
        raise ContentError(f"{path}: field '{field_name}' must be expressed in America/Los_Angeles time")
    return los_angeles_time


def _require_slug(record: dict, path: str) -> str:
    """Return a slug accepted by the existing URL pattern."""
    slug = _require_str(record, "slug", path)
    if re.fullmatch(r"[-\w]+", slug) is None:
        raise ContentError(f"{path}: field 'slug' must contain only letters, numbers, underscores, and hyphens")
    return slug


def _optional_slug(record: dict, path: str) -> str:
    """Return an optional URL slug accepted by the talk detail route."""
    value = _optional_str(record, "slug", path)
    if value and re.fullmatch(r"[-\w]+", value) is None:
        raise ContentError(f"{path}: field 'slug' must contain only letters, numbers, underscores, and hyphens")
    return value


def _optional_wordpress_id(record: dict, path: str) -> int | None:
    """Return an optional positive legacy WordPress ID."""
    value = record.get("wordpress_id")
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ContentError(f"{path}: field 'wordpress_id' must be a positive integer")
    return value


def _split_front_matter(content: str, path: str) -> tuple[str, str]:
    """Split YAML front matter from a Markdown body without changing its HTML."""
    if not content.startswith("---\n"):
        raise ContentError(f"{path}: Markdown posts must begin with YAML front matter")
    end_marker = content.find("\n---\n", len("---\n"))
    if end_marker == -1:
        raise ContentError(f"{path}: Markdown post front matter is not closed")
    return content[len("---\n") : end_marker], content[end_marker + len("\n---\n") :]


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
        archive_url = _optional_str(record, "archive_url", label)
        archive_exemption = _optional_str(record, "archive_exemption", label)
        catalog_title = _optional_str(record, "catalog_title", label)
        link_url = _optional_str(record, "link_url", label)
        if link_url:
            _validate_http_url(link_url, "link_url", f"{label}: clip '{title}'")
        if archive_url:
            parsed_archive_url = urlparse(archive_url)
            if (
                parsed_archive_url.scheme not in {"http", "https"}
                or parsed_archive_url.netloc != "web.archive.org"
                or any(char.isspace() for char in archive_url)
            ):
                raise ContentError(
                    f"{label}: clip '{title}' archive_url must be a web.archive.org HTTP(S) URL, got {archive_url!r}"
                )
        if archive_url and archive_exemption:
            raise ContentError(f"{label}: clip '{title}' cannot have both archive_url and archive_exemption")
        clips.append(
            Clip(
                title=title,
                type=clip_type,
                date=date,
                url=url,
                archive_url=archive_url,
                archive_exemption=archive_exemption,
                catalog_title=catalog_title,
                link_url=link_url,
            )
        )
    clips.sort(key=lambda c: c.date, reverse=True)
    return clips


def load_apps(path: Path | None = None) -> list[App]:
    """Load and validate standalone apps from YAML."""
    if path is None:
        path = CONTENT_PATH / "apps.yaml"
    label = str(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ContentError(f"{label}: top-level structure must be a mapping")
    items = raw.get("apps", [])
    if not isinstance(items, list):
        raise ContentError(f"{label}: 'apps' must be a list")
    seen_urls: set[str] = set()
    apps: list[App] = []
    for record in items:
        if not isinstance(record, dict):
            raise ContentError(f"{label}: each app must be a mapping, got {record!r}")
        title = _require_str(record, "title", label)
        app_type = _require_str(record, "type", label)
        if app_type not in APP_TYPES:
            raise ContentError(f"{label}: app '{title}' type '{app_type}' must be one of {sorted(APP_TYPES)}")
        url = _require_http_url(record, "url", label)
        if url in seen_urls:
            raise ContentError(f"{label}: duplicate app URL '{url}'")
        seen_urls.add(url)
        description = _optional_str(record, "description", label)
        apps.append(App(title=title, type=app_type, url=url, description=description))
    return apps


def group_apps(apps: Sequence[App]) -> list[AppCategory]:
    """Group apps into the display order used on the Apps page."""
    return [
        AppCategory(title=label, object_list=matching_apps)
        for app_type, label in APP_TYPE_LABELS.items()
        if (matching_apps := [app for app in apps if app.type == app_type])
    ]


def load_clip_updates(clip_type: str, catalog: Sequence[App | CodeProject | Doc]) -> list[Clip]:
    """Return dated work records not already represented in a catalog."""
    catalog_titles = {item.title.casefold() for item in catalog}
    catalog_urls = {item.url for item in catalog}
    catalog_urls.update(item.repository_url for item in catalog if isinstance(item, Doc) and item.repository_url)
    return [
        clip
        for clip in load_clips()
        if clip.type == clip_type
        and (clip.catalog_title or clip.title).casefold() not in catalog_titles
        and clip.url not in catalog_urls
    ]


def load_code(path: Path | None = None) -> list[CodeProject]:
    """Load and validate the open-source code catalog."""
    if path is None:
        path = CONTENT_PATH / "code.yaml"
    label = str(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ContentError(f"{label}: top-level structure must be a mapping")
    items = raw.get("code", [])
    if not isinstance(items, list):
        raise ContentError(f"{label}: 'code' must be a list")
    seen_titles: set[str] = set()
    seen_urls: set[str] = set()
    projects: list[CodeProject] = []
    for record in items:
        if not isinstance(record, dict):
            raise ContentError(f"{label}: each code project must be a mapping, got {record!r}")
        title = _require_str(record, "title", label)
        title_key = title.casefold()
        if title_key in seen_titles:
            raise ContentError(f"{label}: duplicate code project title '{title}'")
        seen_titles.add(title_key)
        project_type = _require_str(record, "type", label)
        if project_type not in CODE_TYPES:
            raise ContentError(
                f"{label}: code project '{title}' type '{project_type}' must be one of {sorted(CODE_TYPES)}"
            )
        url = _require_http_url(record, "url", label)
        if url in seen_urls:
            raise ContentError(f"{label}: duplicate code project URL '{url}'")
        seen_urls.add(url)
        description = _optional_str(record, "description", label)
        projects.append(CodeProject(title=title, type=project_type, url=url, description=description))
    projects.sort(key=lambda project: project.title.casefold())
    return projects


def group_code(projects: Sequence[CodeProject]) -> list[CodeCategory]:
    """Group code projects using the sections from the GitHub README."""
    return [
        CodeCategory(title=label, object_list=matching_projects)
        for project_type, label in CODE_TYPE_LABELS.items()
        if (matching_projects := [project for project in projects if project.type == project_type])
    ]


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
    seen_slugs: set[str] = set()
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
        slug = _optional_slug(record, label)
        if slug in seen_slugs:
            raise ContentError(f"{label}: duplicate talk slug '{slug}'")
        if slug:
            seen_slugs.add(slug)
        talks.append(
            Talk(
                title=title,
                venue=venue,
                location=location,
                date=date,
                video_url=video_url,
                local_video_url=_optional_str(record, "local_video_url", label),
                slides_url=slides_url,
                slug=slug,
                short_title=_optional_str(record, "short_title", label),
                deck_url=_optional_str(record, "deck_url", label),
                pdf_url=_optional_str(record, "pdf_url", label),
                notes_url=_optional_str(record, "notes_url", label),
                notes_template=_optional_str(record, "notes_template", label),
                notes_text_url=_optional_str(record, "notes_text_url", label),
                transcript_url=_optional_str(record, "transcript_url", label),
                transcript_template=_optional_str(record, "transcript_template", label),
                transcript_text_url=_optional_str(record, "transcript_text_url", label),
                captions_url=_optional_str(record, "captions_url", label),
                poster_url=_optional_str(record, "poster_url", label),
                original_slides_url=_optional_str(record, "original_slides_url", label),
                original_video_url=_optional_str(record, "original_video_url", label),
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
    seen_repository_urls: set[str] = set()
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
        repository_url = _optional_http_url(record, "repository_url", label, title)
        if repository_url:
            if repository_url in seen_repository_urls:
                raise ContentError(f"{label}: duplicate doc repository_url '{repository_url}' for doc '{title}'")
            seen_repository_urls.add(repository_url)
        docs.append(
            Doc(
                title=title,
                type=doc_type,
                url=url,
                description=description,
                repository_url=repository_url,
            )
        )
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


def load_posts(path: Path | None = None) -> list[MarkdownPost]:
    """Load validated public Markdown posts, newest publication first."""
    if path is None:
        path = CONTENT_PATH / "posts"
    if not path.is_dir():
        raise ContentError(f"{path}: post content directory does not exist")

    posts: list[MarkdownPost] = []
    seen_slugs: set[str] = set()
    seen_url_keys: set[tuple[datetime.date, str]] = set()
    for post_path in sorted(path.glob("*.md")):
        label = str(post_path)
        with post_path.open(encoding="utf-8", newline="") as post_file:
            front_matter, body_markup = _split_front_matter(post_file.read(), label)
        try:
            record = yaml.safe_load(front_matter)
        except yaml.YAMLError as error:
            raise ContentError(f"{label}: invalid YAML front matter") from error
        if not isinstance(record, dict):
            raise ContentError(f"{label}: front matter must be a mapping")
        unexpected_fields = set(record) - POST_FRONT_MATTER_FIELDS
        if unexpected_fields:
            raise ContentError(f"{label}: unsupported front matter fields {sorted(unexpected_fields)}")

        title = _require_str(record, "title", label)
        slug = _require_slug(record, label)
        published_at = _require_los_angeles_datetime(record, "published_at", label)
        repr_image = _optional_str(record, "repr_image", label)
        wordpress_id = _optional_wordpress_id(record, label)

        if slug in seen_slugs:
            raise ContentError(f"{label}: duplicate post slug '{slug}'")
        seen_slugs.add(slug)
        url_key = (published_at.date(), slug)
        if url_key in seen_url_keys:
            raise ContentError(f"{label}: duplicate post publication-date/slug key '{url_key}'")
        seen_url_keys.add(url_key)
        posts.append(
            MarkdownPost(
                title=title,
                slug=slug,
                published_at=published_at,
                body_markup=body_markup,
                repr_image=repr_image,
                wordpress_id=wordpress_id,
            )
        )
    posts.sort(key=lambda post: post.published_at, reverse=True)
    return posts
