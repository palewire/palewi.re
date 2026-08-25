"""Tests for the safe public-post authoring command."""

from pathlib import Path

import pytest
from click.testing import CliRunner
from django.core.management import call_command
from django.test import override_settings

from coltrane import bakery_views, feeds, sitemaps
from coltrane.content_loaders import load_posts
from scripts import new_post


def run_new_post(posts_path: Path, title: str = "A new post", published_at: str = "2026-08-24T09:00:00-07:00"):
    return CliRunner().invoke(
        new_post.cli,
        [
            "--title",
            title,
            "--published-at",
            published_at,
            "--posts-path",
            str(posts_path),
        ],
    )


def test_new_post_creates_loader_compatible_raw_html_file(tmp_path):
    posts_path = tmp_path / "posts"
    posts_path.mkdir()

    result = run_new_post(posts_path, title="Café: New post!")

    destination = posts_path / "2026-08-24--cafe-new-post.md"
    assert result.exit_code == 0, result.output
    assert f"Created {destination}" in result.output
    assert "make check" in result.output
    assert destination.read_text(encoding="utf-8") == (
        "---\n"
        "title: 'Café: New post!'\n"
        "slug: cafe-new-post\n"
        "published_at: '2026-08-24T09:00:00-07:00'\n"
        "---\n"
        "<!-- Replace this placeholder with the published post body in raw HTML. -->\n"
        "<p>Write your post body as raw HTML.</p>\n"
    )
    post = load_posts(posts_path)[0]
    assert post.get_absolute_url() == "/posts/2026/08/24/cafe-new-post/"


@pytest.mark.parametrize(
    ("title", "published_at", "message"),
    [
        ("", "2026-08-24T09:00:00-07:00", "title must not be empty"),
        ("!!!", "2026-08-24T09:00:00-07:00", "URL-safe slug"),
        ("Example", "2026-02-30T09:00:00-08:00", "ISO 8601 datetime"),
        ("Example", "2026-08-24T09:00:00", "timezone offset"),
        ("Example", "2026-08-24T09:00:00+00:00", "America/Los_Angeles"),
    ],
)
def test_new_post_rejects_invalid_input_without_writing(tmp_path, title, published_at, message):
    posts_path = tmp_path / "posts"
    posts_path.mkdir()

    result = run_new_post(posts_path, title, published_at)

    assert result.exit_code == 1
    assert message in result.output
    assert list(posts_path.iterdir()) == []


def test_new_post_rejects_duplicate_slug_without_writing(tmp_path):
    posts_path = tmp_path / "posts"
    posts_path.mkdir()
    (posts_path / "2025-01-01--shared-title.md").write_text(
        "---\ntitle: Shared title\nslug: shared-title\npublished_at: '2025-01-01T09:00:00-08:00'\n---\n<p>Old</p>\n",
        encoding="utf-8",
    )

    result = run_new_post(posts_path, "Shared title", "2026-08-24T09:00:00-07:00")

    assert result.exit_code == 1
    assert "duplicate post slug 'shared-title'" in result.output
    assert [path.name for path in posts_path.iterdir()] == ["2025-01-01--shared-title.md"]


def test_new_post_rejects_duplicate_public_url_without_writing(tmp_path):
    posts_path = tmp_path / "posts"
    posts_path.mkdir()
    (posts_path / "existing.md").write_text(
        "---\ntitle: Shared title\nslug: shared-title\npublished_at: '2026-08-24T09:00:00-07:00'\n---\n<p>Old</p>\n",
        encoding="utf-8",
    )

    result = run_new_post(posts_path, "Shared title", "2026-08-24T09:00:00-07:00")

    assert result.exit_code == 1
    assert "duplicate public URL '/posts/2026/08/24/shared-title/'" in result.output
    assert [path.name for path in posts_path.iterdir()] == ["existing.md"]


def test_new_post_refuses_existing_destination_without_writing(tmp_path):
    posts_path = tmp_path / "posts"
    posts_path.mkdir()
    destination = posts_path / "2026-08-24--example.md"
    destination.write_text("keep this file unchanged", encoding="utf-8")

    result = run_new_post(posts_path, "Example", "2026-08-24T09:00:00-07:00")

    assert result.exit_code == 1
    assert "destination already exists" in result.output
    assert destination.read_text(encoding="utf-8") == "keep this file unchanged"


def test_write_new_file_refuses_a_destination_created_during_write(tmp_path):
    destination = tmp_path / "post.md"
    destination.write_text("keep this file unchanged", encoding="utf-8")

    with pytest.raises(new_post.PostAuthoringError, match="destination already exists"):
        new_post.write_new_file(destination, "new content")

    assert destination.read_text(encoding="utf-8") == "keep this file unchanged"
    assert list(tmp_path.iterdir()) == [destination]


def test_new_post_builds_at_its_public_url(tmp_path, monkeypatch):
    posts_path = tmp_path / "posts"
    posts_path.mkdir()
    result = run_new_post(posts_path)
    assert result.exit_code == 0, result.output
    post = load_posts(posts_path)[0]

    monkeypatch.setattr(bakery_views, "load_posts", lambda: [post])
    monkeypatch.setattr(feeds, "load_posts", lambda: [post])
    monkeypatch.setattr(sitemaps, "load_posts", lambda: [post])
    build_dir = tmp_path / "dist"
    with override_settings(BUILD_DIR=str(build_dir)):
        call_command("build")

    assert (build_dir / "posts/2026/08/24/a-new-post/index.html").is_file()
