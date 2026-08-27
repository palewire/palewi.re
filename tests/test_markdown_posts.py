"""Tests for the public Markdown post archive."""

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from django.conf import settings
from django.utils import timezone

from coltrane.content_loaders import ContentError, load_posts
from coltrane.utils.pygmenter import pygmenter
from scripts.export_posts import validate_export_paths

CONTENT_PATH = Path(__file__).resolve().parent.parent / "coltrane" / "content"
POSTS_PATH = CONTENT_PATH / "posts"
MANIFEST_PATH = CONTENT_PATH / "posts-manifest.json"
LOS_ANGELES = ZoneInfo("America/Los_Angeles")


def load_manifest() -> dict:
    """Read the public-only export manifest."""
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_historical_markdown_posts_match_public_export_manifest():
    """Every historical export file and its lossless body match the fingerprint."""
    manifest = load_manifest()
    manifest_posts = manifest["posts"]
    expected_paths = {entry["path"] for entry in manifest_posts}
    actual_paths = {f"posts/{path.name}" for path in POSTS_PATH.glob("*.md")}
    assert manifest["post_count"] == 72
    assert len(manifest_posts) == 72
    assert expected_paths.issubset(actual_paths)
    assert manifest["production_inventory"] == {"total": 166, "live": 72, "draft": 94, "hidden": 0}

    fingerprint = hashlib.sha256(
        json.dumps(manifest_posts, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    assert fingerprint == manifest["posts_fingerprint_sha256"]

    posts_by_permalink = {post.get_absolute_url(): post for post in load_posts()}
    assert {entry["permalink"] for entry in manifest_posts}.issubset(posts_by_permalink)
    for entry in manifest_posts:
        post_path = CONTENT_PATH / entry["path"]
        assert hashlib.sha256(post_path.read_bytes()).hexdigest() == entry["sha256"]
        assert (
            hashlib.sha256(posts_by_permalink[entry["permalink"]].body_markup.encode()).hexdigest()
            == entry["body_sha256"]
        )


def test_markdown_posts_have_unique_slugs_and_preserved_permalinks():
    """Posts retain globally unique slugs and date URLs."""
    posts = load_posts()
    assert len(posts) >= 72
    assert len({post.slug for post in posts}) == len(posts)
    assert len({(post.published_at.date(), post.slug) for post in posts}) == len(posts)

    manifest_permalinks = {entry["permalink"] for entry in load_manifest()["posts"]}
    assert manifest_permalinks.issubset({post.get_absolute_url() for post in posts})


def test_markdown_posts_keep_los_angeles_publication_datetimes():
    """The front matter preserves the original Los Angeles local clock time."""
    manifest_by_permalink = {entry["permalink"]: entry for entry in load_manifest()["posts"]}
    for post in load_posts():
        assert timezone.is_aware(post.published_at)
        assert post.published_at.tzinfo == LOS_ANGELES
        assert post.get_absolute_url().startswith(f"/posts/{post.published_at:%Y/%m/%d}/")
        if expected := manifest_by_permalink.get(post.get_absolute_url()):
            assert post.published_at == datetime.fromisoformat(expected["published_at"])


def test_django_uses_timezone_aware_datetimes():
    assert settings.USE_TZ is True


def test_markdown_posts_preserve_legacy_pre_lang_markup():
    """Raw HTML bodies retain code markup and receive semantic highlighting."""
    legacy_posts = [post for post in load_posts() if re.search(r"<pre\s+[^>]*\blang=", post.body_markup)]
    assert len(legacy_posts) == load_manifest()["legacy_pre_lang_post_count"] == 25

    python_post = next(post for post in legacy_posts if '<pre lang="python">' in post.body_markup)
    assert '<pre lang="python">' in python_post.body_markup
    highlighted = pygmenter(python_post.body_markup)
    assert '<div class="source" data-language="Python">' in highlighted
    assert '<pre aria-label="Python code"><code class="language-python">' in highlighted
    assert "&lt;div class=" not in highlighted


def test_markdown_post_requires_los_angeles_datetime(tmp_path):
    """UTC front matter is rejected even when it represents the same instant."""
    post_path = tmp_path / "post.md"
    post_path.write_text(
        "---\ntitle: Example\nslug: example\npublished_at: '2025-01-01T20:00:00+00:00'\n---\n<p>Body</p>",
        encoding="utf-8",
    )

    with pytest.raises(ContentError, match="America/Los_Angeles"):
        load_posts(tmp_path)


def test_markdown_post_requires_an_aware_datetime(tmp_path):
    post_path = tmp_path / "post.md"
    post_path.write_text(
        "---\ntitle: Example\nslug: example\npublished_at: '2025-01-01T12:00:00'\n---\n<p>Body</p>",
        encoding="utf-8",
    )

    with pytest.raises(ContentError, match="timezone offset"):
        load_posts(tmp_path)


@pytest.mark.parametrize(
    ("published_at", "fold", "utc_time"),
    [
        ("2025-11-02T01:30:00-07:00", 0, "2025-11-02T08:30:00+00:00"),
        ("2025-11-02T01:30:00-08:00", 1, "2025-11-02T09:30:00+00:00"),
    ],
)
def test_markdown_post_preserves_each_ambiguous_los_angeles_time(tmp_path, published_at, fold, utc_time):
    post_path = tmp_path / "post.md"
    post_path.write_text(
        f"---\ntitle: Example\nslug: example\npublished_at: '{published_at}'\n---\n<p>Body</p>",
        encoding="utf-8",
    )

    post = load_posts(tmp_path)[0]

    assert post.published_at.fold == fold
    assert post.published_at.astimezone(UTC).isoformat() == utc_time


def test_markdown_post_rejects_nonexistent_los_angeles_time(tmp_path):
    post_path = tmp_path / "post.md"
    post_path.write_text(
        "---\ntitle: Example\nslug: example\npublished_at: '2025-03-09T02:30:00-08:00'\n---\n<p>Body</p>",
        encoding="utf-8",
    )

    with pytest.raises(ContentError, match="America/Los_Angeles"):
        load_posts(tmp_path)


def test_markdown_post_rejects_unknown_front_matter(tmp_path):
    """The authoring contract rejects accidental metadata fields."""
    post_path = tmp_path / "post.md"
    post_path.write_text(
        "---\ntitle: Example\nslug: example\npublished_at: '2025-01-01T12:00:00-08:00'\nstatus: draft\n---\n<p>Body</p>",
        encoding="utf-8",
    )

    with pytest.raises(ContentError, match="unsupported"):
        load_posts(tmp_path)


def test_markdown_post_rejects_duplicate_slug(tmp_path):
    """Slugs must remain globally unique before file-backed routing is enabled."""
    for name in ("one.md", "two.md"):
        (tmp_path / name).write_text(
            "---\ntitle: Example\nslug: example\npublished_at: '2025-01-01T12:00:00-08:00'\n---\n<p>Body</p>",
            encoding="utf-8",
        )

    with pytest.raises(ContentError, match="duplicate post slug"):
        load_posts(tmp_path)


def test_exporter_rejects_archive_path_inside_public_repository():
    """The export command cannot write draft records into this checkout."""
    with pytest.raises(ValueError, match="outside the public repository"):
        validate_export_paths(CONTENT_PATH / "private-archive", CONTENT_PATH)
