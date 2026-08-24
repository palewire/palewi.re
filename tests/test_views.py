"""Tests for public-facing pages and redirects."""

from unittest.mock import patch

import pytest
from django.db import DatabaseError
from django.test import Client
from django.test.utils import override_settings

from coltrane.views import server_error


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
def test_bio_page_context_includes_fixed_current_site(client):
    response = client.get("/who-is-ben-welsh/")
    assert response.status_code == 200
    assert any(context.get("current_site") == "palewi.re" for context in response.context)


@pytest.mark.django_db
def test_bio_page_footer_links_to_main_commit(client):
    commit = "0123456789abcdef0123456789abcdef01234567"

    with patch("toolbox.context_processors._main_commit", return_value=commit):
        response = client.get("/who-is-ben-welsh/")

    content = response.content.decode()
    assert f'href="https://github.com/palewire/palewi.re/commit/{commit}"' in content
    assert ">0123456</a>" in content


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
def test_scrape_album_2006_returns_not_found(client):
    response = client.get("/scrape/albums/2006.html")
    assert response.status_code == 404


@pytest.mark.django_db
def test_openlayers_tutorial_returns_not_found(client):
    response = client.get("/openlayers-proportional-symbols/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_mack_redirect_still_exists(client):
    response = client.get("/mack/")
    assert response.status_code in (301, 302)
    assert response["Location"] == "https://web.archive.org/web/20121109101143/http://palewi.re/mack/"


@pytest.mark.django_db
def test_candysays_redirect_points_to_wayback(client):
    response = client.get("/candysays/")
    assert response.status_code in (301, 302)
    assert response["Location"] == "https://web.archive.org/web/20160413123742/http://palewi.re/candysays/"


@pytest.mark.django_db
def test_legacy_images_redirect_directly_to_s3(client):
    response = client.get("/images/test.jpg")
    assert response.status_code in (301, 302)
    assert response["Location"] == "https://palewire.s3.amazonaws.com/img/test.jpg"


@pytest.mark.django_db
def test_favicon_route_exists(client):
    response = client.get("/favicon.ico")
    assert response.status_code in (200, 301, 302)
    if response.status_code in (301, 302):
        assert response["Location"].endswith("/static/favicon.ico")


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_not_found_page_uses_simplified_message(client):
    response = client.get("/this-page-does-not-exist/")

    assert response.status_code == 404
    content = response.content.decode()
    assert "<title>Page not found · palewire</title>" in content
    assert '<meta name="robots" content="noindex" />' in content
    assert '<h1 id="error-heading">404</h1>' in content
    assert "This page could not be found." in content


@pytest.mark.django_db
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
    response = client.get(path)
    assert response.status_code == 404


@override_settings(DEBUG=False)
def test_server_error_page_uses_simplified_message(rf):
    response = server_error(rf.get("/"))

    assert response.status_code == 500
    content = response.content.decode()
    assert "<title>Server error · palewire</title>" in content
    assert '<meta name="robots" content="noindex" />' in content
    assert '<h1 id="error-heading">500</h1>' in content
    assert "Something went wrong. Please try again later." in content


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


# ---------------------------------------------------------------------------
# DomainRedirectMiddleware regression tests
# ---------------------------------------------------------------------------


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


@pytest.mark.django_db
def test_canonical_host_is_not_redirected(client):
    """Requests arriving on palewi.re itself are served normally."""
    response = client.get("/who-is-ben-welsh/")
    assert response.status_code == 200
