"""Tests for public-facing pages and redirects."""

from unittest.mock import patch

import pytest
from django.db import DatabaseError
from django.test import Client
from django.test.utils import override_settings


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def test_root_redirects_to_bio(client):
    response = client.get("/")
    assert response.status_code in (301, 302)
    assert "/who-is-ben-welsh/" in response["Location"]


@pytest.mark.django_db
def test_bio_page_ok(client):
    response = client.get("/who-is-ben-welsh/")
    assert response.status_code == 200
    content = response.content.decode()
    assert 'width="800"' in content
    assert 'height="450"' in content
    assert 'fetchpriority="high"' in content


@pytest.mark.django_db
def test_work_list_ok(client):
    response = client.get("/work/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_talks_list_ok(client):
    response = client.get("/talks/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_posts_list_ok(client):
    response = client.get("/posts/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_docs_list_ok(client):
    response = client.get("/docs/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_bots_list_ok(client):
    response = client.get("/bots/")
    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_not_found_page_offers_navigation(client):
    response = client.get("/this-page-does-not-exist/")

    assert response.status_code == 404
    content = response.content.decode()
    assert "<title>Page not found · palewire</title>" in content
    assert '<meta name="robots" content="noindex" />' in content
    assert 'href="/">Go to the homepage' in content
    assert 'href="/posts/">Posts</a>' in content


@pytest.mark.django_db
def test_health_check_ok(client):
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] is True


def test_health_check_reports_database_failure(client):
    with patch("toolbox.views.connection.ensure_connection", side_effect=DatabaseError):
        response = client.get("/health/")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "db": False}


@pytest.mark.django_db
def test_robots_txt_ok(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200


@pytest.mark.django_db
def test_sitemap_index_ok(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
