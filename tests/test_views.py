"""Tests for public-facing pages and redirects."""

from unittest.mock import patch

import pytest
from django.test import Client
from django.test.utils import override_settings

from coltrane.views import server_error
from project.redirects import STATIC_REDIRECTS


@pytest.fixture
def client():
    return Client()


def test_root_redirects_to_bio(client):
    response = client.get("/")
    assert response.status_code in (301, 302)
    assert "/who-is-ben-welsh/" in response["Location"]


def test_bio_page_ok(client):
    response = client.get("/who-is-ben-welsh/")
    assert response.status_code == 200
    content = response.content.decode()
    assert 'width="800"' in content
    assert 'height="450"' in content
    assert 'fetchpriority="high"' in content


def test_bio_page_context_includes_fixed_current_site(client):
    response = client.get("/who-is-ben-welsh/")
    assert response.status_code == 200
    assert any(context.get("current_site") == "palewi.re" for context in response.context)


def test_bio_page_footer_links_to_main_commit(client):
    commit = "0123456789abcdef0123456789abcdef01234567"

    with patch("toolbox.context_processors._main_commit", return_value=commit):
        response = client.get("/who-is-ben-welsh/")

    content = response.content.decode()
    assert f'href="https://github.com/palewire/palewi.re/commit/{commit}"' in content
    assert ">0123456</a>" in content


@pytest.mark.parametrize("page", ["/work/", "/talks/", "/posts/", "/docs/", "/bots/"])
def test_public_list_pages_are_available_without_database(client, page):
    assert client.get(page).status_code == 200


@pytest.mark.parametrize("page", ["/scrape/albums/2006.html", "/openlayers-proportional-symbols/"])
def test_removed_pages_return_not_found(client, page):
    assert client.get(page).status_code == 404


@pytest.mark.parametrize(("source", "destination"), STATIC_REDIRECTS.items())
def test_static_legacy_redirects_remain_stable(client, source, destination):
    response = client.get(f"/{source}?source=test")
    assert response.status_code in (301, 302)
    assert response["Location"] == destination


@pytest.mark.parametrize(
    ("source", "destination"),
    [
        ("/tag/django/", "/who-is-ben-welsh/"),
        ("/tags/django/", "/who-is-ben-welsh/"),
        ("/happyhours/old/", "/"),
        ("/images/test.jpg", "https://palewire.s3.amazonaws.com/img/test.jpg"),
        ("/applications/legacy/page/", "/apps/legacy/page/"),
        ("/apps/page/2/", "/apps/"),
        ("/posts/page/2/", "/posts/"),
        ("/2009/09/01/test-post/", "/posts/2009/09/01/test-post/"),
    ],
)
def test_dynamic_legacy_redirects_remain_stable(client, source, destination):
    response = client.get(source)
    assert response.status_code in (301, 302)
    assert response["Location"] == destination


def test_favicon_route_exists(client):
    response = client.get("/favicon.ico")
    assert response.status_code in (200, 301, 302)
    if response.status_code in (301, 302):
        assert response["Location"].endswith("/static/favicon.ico")


@override_settings(DEBUG=False)
def test_not_found_page_uses_simplified_message(client):
    response = client.get("/this-page-does-not-exist/")

    assert response.status_code == 404
    content = response.content.decode()
    assert "<title>Page not found · palewire</title>" in content
    assert '<meta name="robots" content="noindex" />' in content
    assert '<h1 id="error-heading">404</h1>' in content
    assert "This page could not be found." in content


@pytest.mark.parametrize(
    "path",
    [
        "/books/",
        "/books/page/2/",
        "/commits/",
        "/links/",
        "/locations/",
        "/movies/",
        "/photos/",
        "/shouts/",
        "/tracks/",
        "/ticker/",
        "/ticker/page/2/",
        "/categories/list/",
    ],
)
def test_retired_legacy_pages_return_not_found(client, path):
    assert client.get(path).status_code == 404


@override_settings(DEBUG=False)
def test_server_error_page_uses_simplified_message(rf):
    response = server_error(rf.get("/"))

    assert response.status_code == 500
    content = response.content.decode()
    assert "<title>Server error · palewire</title>" in content
    assert '<meta name="robots" content="noindex" />' in content
    assert '<h1 id="error-heading">500</h1>' in content
    assert "Something went wrong. Please try again later." in content


def test_health_check_ok(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_robots_txt_ok(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert "admin" not in response.content.decode()


def test_sitemap_index_ok(client):
    assert client.get("/sitemap.xml").status_code == 200


@pytest.mark.parametrize("host", ["palewire.com", "www.palewire.com", "www.palewi.re"])
def test_domain_redirect_middleware_redirects_sibling_domains(host, settings):
    """Requests arriving on sibling domains are permanently redirected to palewi.re."""
    settings.ALLOWED_HOSTS = [host]
    client = Client(SERVER_NAME=host)
    response = client.get("/who-is-ben-welsh/")
    assert response.status_code == 301
    location = response["Location"]
    assert "palewi.re" in location
    assert host not in location


def test_canonical_host_is_not_redirected(client):
    """Requests arriving on palewi.re itself are served normally."""
    assert client.get("/who-is-ben-welsh/").status_code == 200
