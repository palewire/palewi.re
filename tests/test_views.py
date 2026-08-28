"""Tests for public-facing pages and redirects."""

from unittest.mock import patch
from xml.etree import ElementTree

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


@pytest.mark.parametrize(
    "page",
    ["/posts/", "/clips/", "/apps/", "/code/", "/guides/", "/talks/", "/bots/"],
)
def test_public_list_pages_are_available_without_database(client, page):
    assert client.get(page).status_code == 200


def test_mobile_navigation_has_menu_disclosure(client):
    content = client.get("/apps/").content.decode()
    assert content.count("<nav") == 1
    assert '<nav aria-label="Primary">' in content
    assert '<div class="nav-menu">' in content
    assert 'popovertarget="mobile-nav-links"' in content
    assert '<div id="mobile-nav-links" class="nav-drawer" popover>' in content
    assert 'aria-label="Close menu"' in content
    assert '<span class="hamburger" aria-hidden="true">' in content


def test_bots_omit_empty_twitter_link(client):
    content = client.get("/bots/").content.decode()

    assert (
        '@RandomPigeonGPT (<a target="_blank" href="https://mastodon.palewi.re/@RandomPigeonGPT">Mastodon &raquo;</a>)'
        in content
    )
    assert 'href="">Twitter' not in content
    assert 'href="https://twitter.com/divineanndvorak">Twitter &raquo;</a>' in content


@pytest.mark.parametrize(("old_path", "new_path"), [("/work/", "/clips/")])
def test_replaced_list_pages_redirect(client, old_path, new_path):
    response = client.get(old_path)
    assert response.status_code == 302
    assert response["Location"] == new_path


def test_docs_page_points_to_separate_catalogs(client):
    content = client.get("/docs/").content.decode()
    assert 'href="/code/"' in content
    assert 'href="/guides/"' in content


def test_work_records_route_to_their_new_sections(client):
    content = client.get("/clips/").content.decode()
    assert "Journalism lost its culture of sharing" in content
    assert "How to deploy a Prefect agent to Google Kubernetes Engine" in content
    assert "How to push tagged Docker releases" in content
    assert "Tracking Trump" in content
    assert "Reuters Climate Monitor" in content
    assert "geodataframe-to-pmtiles" not in content
    assert "RandomPigeonGPT" not in content
    assert "The decline of open-source news" not in content
    assert "Min-Max Rescaling Calculator" not in content
    assert "Data loader to generate PNG from canvas" not in content
    assert "How Reuters uses Datawrapper" not in content
    assert "Ipsos credibility interval calculator" not in content
    assert "is 5" not in content
    assert "@DivineAnnDvorak" not in content

    apps = client.get("/apps/").content.decode()
    assert "Services" not in apps
    assert "Archiving" in apps
    assert "Databases" in apps
    assert "Social media bots" in apps
    assert "Personal websites" in apps
    assert "Wheel of Feedback" not in apps
    assert "Datawrapper MCP" not in apps
    assert "palewi.re data" not in apps
    assert "fivethirtyeightindex" in apps
    assert "AMSAT Satellite Index" in apps
    assert "Random Pigeon GPT" not in apps
    assert "Reuters Jobs" not in apps
    assert "Save My News" not in apps
    assert "NYC Data Bot" not in apps
    assert "IRE Resource Center" in apps
    assert "the e.e. cummings free poetry archive" in apps
    assert "The News Homepages Archive" in apps
    assert "The Studs Terkel Archive Podcast" in apps
    assert "PastPages" not in apps
    assert "The Studs Terkel Archive Podcast: Season 2" not in apps

    code = client.get("/code/").content.decode()
    assert "air-quality-index" in code
    assert "datawrapper-mcp" in code
    assert "Wheel of Feedback" in code
    assert "Min-Max Rescaling Calculator" in code
    assert "Data loader to generate PNG from canvas" in code
    assert "Ipsos credibility interval calculator" in code
    assert "random-pigeon-gpt" in code
    assert "reuters-jobs" in code
    assert "Save My News" in code
    assert "Updates" not in code
    assert all(section in code for section in ["Data", "Python", "JavaScript", "Other", "Inactive"])

    guides = client.get("/guides/").content.decode()
    assert "First Python Notebook" in guides
    assert 'href="https://palewi.re/docs/first-python-notebook/"' in guides
    assert "First Observable Notebook" in guides
    assert "Lessons" not in guides
    assert "Updates" not in guides
    assert "First LLM Classifier at Hugging Face" not in guides


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
    ("path", "status_code"),
    [
        *(
            (
                f"/{rule.source}",
                200 if rule.source in {"apps/", "clips/"} else 302 if rule.source == "work/" else 404,
            )
            for rule in RULES
            if not rule.is_dynamic
        ),
        *((example, 404) for rule in RULES if rule.is_dynamic for example in rule.examples),
    ],
)
def test_legacy_manifest_paths_have_expected_django_status(client, path, status_code):
    assert client.get(f"{path}?source=test").status_code == status_code


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


def test_static_sitemap_lists_every_public_list_page(client):
    response = client.get("/sitemap-static.xml")

    assert response.status_code == 200
    root = ElementTree.fromstring(response.content)
    namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = {entry.findtext("sitemap:loc", namespaces=namespace) for entry in root.findall("sitemap:url", namespace)}
    assert urls == {
        "http://testserver/who-is-ben-welsh/",
        "http://testserver/posts/",
        "http://testserver/clips/",
        "http://testserver/apps/",
        "http://testserver/code/",
        "http://testserver/docs/",
        "http://testserver/guides/",
        "http://testserver/talks/",
        "http://testserver/bots/",
    }
