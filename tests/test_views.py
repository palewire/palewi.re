"""Tests for public-facing pages and redirects."""

from unittest.mock import patch

import pytest
from django.templatetags.static import static
from django.test import Client
from django.test.utils import override_settings
from django.urls import include, path

from project.redirect_manifest import RULES


def failing_view(_request):
    raise RuntimeError("Expected test error")


urlpatterns = [path("", include("project.urls")), path("failing/", failing_view)]


@pytest.fixture
def client():
    return Client()


def test_root_redirects_to_bio(client):
    response = client.get("/")
    assert response.status_code in (301, 302)
    assert response["Location"] == "/who-is-ben-welsh/"


def test_bio_page_ok(client):
    response = client.get("/who-is-ben-welsh/")
    assert response.status_code == 200
    content = response.content.decode()
    assert 'width="800"' in content
    assert 'height="450"' in content
    assert 'fetchpriority="high"' in content


def test_bio_page_uses_canonical_domain(client):
    response = client.get("/who-is-ben-welsh/")

    assert response.status_code == 200
    content = response.content.decode()
    assert '<link rel="canonical" href="https://palewi.re/who-is-ben-welsh/" />' in content
    assert '"url": "https://palewi.re/who-is-ben-welsh/"' in content


def test_bio_page_footer_links_to_main_commit(client):
    commit = "0123456789abcdef0123456789abcdef01234567"

    with patch("toolbox.context_processors._main_commit", return_value=commit):
        response = client.get("/who-is-ben-welsh/")

    content = response.content.decode()
    assert f'href="https://github.com/palewire/palewi.re/commit/{commit}"' in content
    assert "Revision <a " in content
    assert ">0123456</a>" in content


@pytest.mark.parametrize("page", ["/work/", "/talks/", "/posts/", "/docs/", "/bots/"])
def test_public_list_pages_are_available_without_database(client, page):
    assert client.get(page).status_code == 200


@pytest.mark.parametrize("page", ["/scrape/albums/2006.html", "/openlayers-proportional-symbols/"])
def test_removed_pages_return_not_found(client, page):
    assert client.get(page).status_code == 404


@pytest.mark.parametrize(
    "page",
    [
        "/.well-known/webfinger?resource=acct%3Apalewire%40palewi.re",
        "/.well-known/host-meta",
        "/.well-known/nodeinfo",
    ],
)
def test_django_no_longer_serves_mastodon_discovery_endpoints(client, page):
    assert client.get(page).status_code == 404


@pytest.mark.parametrize(
    "path",
    [
        *(f"/{rule.source}" for rule in RULES if not rule.is_dynamic),
        *(example for rule in RULES if rule.is_dynamic for example in rule.examples),
    ],
)
def test_legacy_manifest_paths_return_not_found_at_django_origin(client, path):
    assert client.get(f"{path}?source=test").status_code == 404


@pytest.mark.parametrize("source", ["/1/02/03/post/", "/2024/2/03/post/", "/2024/02/3/post/"])
def test_malformed_legacy_date_paths_return_not_found(client, source):
    assert client.get(source).status_code == 404


def test_favicon_route_exists(client):
    response = client.get("/favicon.ico")
    assert response.status_code in (200, 301, 302)
    if response.status_code in (301, 302):
        assert response["Location"] == static("favicon.ico")


def test_username_redirect_remains_unchanged(client):
    response = client.get("/@palewire")

    assert response.status_code == 302
    assert response["Location"] == "https://mastodon.palewi.re/@palewire"


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


@override_settings(DEBUG=False, ROOT_URLCONF=__name__)
def test_server_error_page_uses_default_handler():
    response = Client(raise_request_exception=False).get("/failing/")

    assert response.status_code == 500
    content = response.content.decode()
    assert "<title>Server error · palewire</title>" in content
    assert '<meta name="robots" content="noindex" />' in content
    assert '<h1 id="error-heading">500</h1>' in content
    assert "Something went wrong. Please try again later." in content
    assert '<link rel="icon" href="/static/favicon.ico" />' in content


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
