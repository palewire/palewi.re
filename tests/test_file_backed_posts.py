"""Tests for public post views backed solely by checked-in Markdown files."""

import json
import re
import xml.etree.ElementTree as xml
from email.utils import parsedate_to_datetime
from unittest.mock import patch

import pytest
from django.test import Client

from coltrane.content_loaders import load_posts
from coltrane.feeds import plain_text_summary
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


def test_post_detail_loads_soundcloud_iframe_and_highlights_legacy_code(client, public_posts):
    """Stored SoundCloud markup remains a normal iframe that loads without JavaScript."""
    soundcloud_post = next(post for post in public_posts if "w.soundcloud.com/player/" in post.body_markup)
    code_post = next(post for post in public_posts if '<pre lang="python">' in post.body_markup)

    raw_response = client.get(soundcloud_post.get_absolute_url())
    code_response = client.get(code_post.get_absolute_url())

    raw_content = raw_response.content.decode()
    assert "<iframe" in raw_content
    assert 'src="https://w.soundcloud.com/player/' in raw_content
    assert "Load SoundCloud player" not in raw_content
    assert "<template>" not in raw_content
    assert 'class="source"' in code_response.content.decode()


def test_datawrapper_embed_is_responsive_and_spaced(client):
    response = client.get("/posts/2026/01/27/how-journalism-lost-its-culture-of-sharing/")
    content = response.content.decode()

    assert response.status_code == 200
    assert '<div class="chart-embed">' in content
    assert 'id="datawrapper-chart-6T1Lq"' in content
    assert 'data["datawrapper-height"]' in content
    assert content.count('href="https://source.opennews.org/articles/journalism-lost-sharing-culture/"') == 2


def test_podcast_embed_has_accessible_name_and_contrast(client):
    response = client.get("/posts/2025/05/21/ire-podcast-transcript/")
    content = response.content.decode()

    assert response.status_code == 200
    assert 'title="IRE Radio podcast player"' in content
    assert "color: #767676" in content
    assert "<iframe" in content
    assert 'src="https://w.soundcloud.com/player/' in content
    assert "Load SoundCloud player" not in content


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
        json_ld_blocks = re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
            response.content.decode(),
            flags=re.DOTALL,
        )
        assert post.repr_image in [json.loads(block).get("image") for block in json_ld_blocks]


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
    publication_dates = [item.findtext("pubDate") for item in items]
    assert all(publication_date is not None for publication_date in publication_dates)
    assert [parsedate_to_datetime(publication_date) for publication_date in publication_dates if publication_date] == [
        post.published_at.replace(microsecond=0) for post in public_posts[:10]
    ]
    assert [item.findtext("description") for item in items] == [post.body_html for post in public_posts[:10]]


def test_json_feed_contains_every_file_backed_post(client, public_posts):
    """The JSON Feed has stable canonical metadata and every published post."""
    response = client.get("/feeds/posts.json")
    payload = json.loads(response.content)
    expected_urls = [f"https://palewi.re{post.get_absolute_url()}" for post in public_posts]

    assert response.status_code == 200
    assert response["Content-Type"] == "application/feed+json; charset=utf-8"
    assert payload["version"] == "https://jsonfeed.org/version/1.1"
    assert payload["title"] == "palewi.re posts"
    assert payload["home_page_url"] == "https://palewi.re/"
    assert payload["feed_url"] == "https://palewi.re/feeds/posts.json"
    assert [item["id"] for item in payload["items"]] == expected_urls
    assert [item["url"] for item in payload["items"]] == expected_urls
    assert [item["title"] for item in payload["items"]] == [post.title for post in public_posts]
    assert [item["date_published"] for item in payload["items"]] == [
        post.published_at.isoformat() for post in public_posts
    ]
    assert [item["content_html"] for item in payload["items"]] == [post.body_html for post in public_posts]
    assert [item["summary"] for item in payload["items"]] == [
        plain_text_summary(post.body_html) for post in public_posts
    ]


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


@pytest.mark.parametrize(
    "permalink",
    [
        "/posts/2026/01/01/not-a-public-post/",
        "/posts/2008/05/18/bill-oreilly-flips-out-the-ringtone/",
        "/posts/2010/03/10/google-charts-takes-tufte-challenge/",
    ],
)
def test_unknown_post_permalink_returns_not_found(client, permalink):
    """A URL absent from the public files returns the normal 404 response."""
    response = client.get(permalink)

    assert response.status_code == 404


def test_invalid_calendar_date_returns_not_found(client):
    response = client.get("/posts/2025/02/30/example/")

    assert response.status_code == 404
