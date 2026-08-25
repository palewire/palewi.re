"""Tests for public post views backed solely by checked-in Markdown files."""

import xml.etree.ElementTree as xml
from unittest.mock import patch

import pytest
from django.test import Client

from coltrane.content_loaders import load_posts
from coltrane.utils.pygmenter import pygmenter


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def public_posts():
    return load_posts()


def test_all_public_post_permalinks_resolve_without_database(client, public_posts):
    """Every manifest-backed public URL is served from its Markdown file."""
    for post in public_posts:
        response = client.get(post.get_absolute_url())
        assert response.status_code == 200
        assert response.context["object"] == post


def test_post_list_uses_file_order(client, public_posts):
    """The list retains descending Los Angeles publication order from files."""
    response = client.get("/posts/")

    assert response.status_code == 200
    assert list(response.context["object_list"]) == public_posts
    assert response.context["is_paginated"] is False
    content = response.content.decode()
    assert content.index(public_posts[0].get_absolute_url()) < content.index(public_posts[-1].get_absolute_url())


def test_post_detail_progressively_enhances_soundcloud_and_legacy_code_highlighting(client, public_posts):
    """Stored HTML keeps a no-JavaScript SoundCloud fallback and legacy code highlighting."""
    raw_html_post = next(post for post in public_posts if "<iframe" in post.body_markup)
    code_post = next(post for post in public_posts if '<pre lang="python">' in post.body_markup)

    raw_response = client.get(raw_html_post.get_absolute_url())
    code_response = client.get(code_post.get_absolute_url())

    raw_content = raw_response.content.decode()
    assert 'class="soundcloud-embed"' in raw_content
    assert "Load SoundCloud player" in raw_content
    assert "<template><iframe" in raw_content
    assert "<noscript>" in raw_content
    assert "JavaScript is disabled. The SoundCloud player is available below." in raw_content
    assert 'class="source"' in code_response.content.decode()


def test_podcast_embed_has_accessible_name_and_contrast(client):
    response = client.get("/posts/2025/05/21/ire-podcast-transcript/")
    content = response.content.decode()

    assert response.status_code == 200
    assert 'title="IRE Radio podcast player"' in content
    assert "color: #767676" in content
    assert "SoundCloud may set cookies." in content
    assert 'aria-live="polite"' in content


def test_post_html_is_highlighted_once_per_loaded_post(public_posts):
    """Templates can reuse rendered HTML without repeating legacy highlighting."""
    post = next(post for post in public_posts if '<pre lang="python">' in post.body_markup)

    with patch("coltrane.utils.pygmenter.pygmenter", wraps=pygmenter) as mocked_pygmenter:
        assert post.body_html == post.body_html

    mocked_pygmenter.assert_called_once_with(post.body_markup)


def test_post_detail_keeps_representative_image_metadata(client, public_posts):
    """The structured metadata retains each exported representative image."""
    for post in (post for post in public_posts if post.repr_image):
        response = client.get(post.get_absolute_url())
        assert post.repr_image in response.content.decode()


def test_feed_uses_latest_ten_file_backed_posts(client, public_posts):
    """The feed retains the published newest-first ten-post selection."""
    response = client.get("/feeds/posts/")
    root = xml.fromstring(response.content)
    items = root.findall("./channel/item")

    assert response.status_code == 200
    assert [item.findtext("title") for item in items] == [post.title for post in public_posts[:10]]
    assert [item.findtext("link") for item in items] == [
        f"http://testserver{post.get_absolute_url()}" for post in public_posts[:10]
    ]
    assert [item.findtext("pubDate") for item in items] == [None] * 10


def test_sitemap_lists_every_file_backed_post_with_publication_date(client, public_posts):
    """The posts sitemap is complete without database records."""
    response = client.get("/sitemap-posts.xml")
    root = xml.fromstring(response.content)
    namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    entries = root.findall("sitemap:url", namespace)

    assert response.status_code == 200
    assert [entry.findtext("sitemap:loc", namespaces=namespace) for entry in entries] == [
        f"http://testserver{post.get_absolute_url()}" for post in public_posts
    ]
    assert [entry.findtext("sitemap:lastmod", namespaces=namespace) for entry in entries] == [
        post.published_at.date().isoformat() for post in public_posts
    ]


def test_unknown_post_permalink_returns_not_found(client):
    """A URL absent from the public files retains the legacy 404 behavior."""
    response = client.get("/posts/2026/01/01/not-a-public-post/")

    assert response.status_code == 404


def test_invalid_calendar_date_returns_not_found(client):
    response = client.get("/posts/2025/02/30/example/")

    assert response.status_code == 404
