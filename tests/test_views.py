"""Tests for public-facing pages and redirects."""

import hashlib
import json
import re
from html.parser import HTMLParser
from unittest.mock import patch
from xml.etree import ElementTree

import pytest
from django.templatetags.static import static
from django.test import Client
from django.test.utils import override_settings
from django.urls import include, path

from coltrane.content_loaders import load_clips, load_posts, load_talks
from project.redirect_manifest import RULES


def failing_view(_request):
    raise RuntimeError("Expected test error")


urlpatterns = [path("", include("project.urls")), path("failing/", failing_view)]


class MainTextParser(HTMLParser):
    """Collect authored text inside the page's main content."""

    def __init__(self) -> None:
        super().__init__()
        self.in_main = False
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "main" and dict(attrs).get("id") == "bd":
            self.in_main = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "main":
            self.in_main = False

    def handle_data(self, data: str) -> None:
        if self.in_main:
            self.text.append(data)


@pytest.fixture
def client():
    return Client()


def main_text_digest(content: str) -> str:
    """Return a stable checksum of user-visible main content."""
    parser = MainTextParser()
    parser.feed(content)
    parser.close()
    text = " ".join(" ".join(parser.text).split())
    return hashlib.sha256(text.encode()).hexdigest()


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


def test_bio_page_uses_factual_metadata_description(client):
    content = client.get("/who-is-ben-welsh/").content.decode()
    description = "Ben Welsh is a reporter, editor and computer programmer."

    assert content.count(f'content="{description}"') == 3
    assert f'"description": "{description}"' in content
    assert '"@id": "https://palewi.re/who-is-ben-welsh/"' in content


@pytest.mark.parametrize(
    ("page", "expected_description"),
    [
        ("/posts/", "A complete list of articles written for this site."),
        ("/clips/", "My bylines at Reuters, the Los Angeles Times and elsewhere on the World Wide Web."),
        ("/apps/", "My independent network of Internet publications."),
        ("/code/", "Open-source computer programming packages and projects."),
        ("/guides/", "Practical guides for data journalists."),
        ("/docs/", "Documentation for my open-source software and teaching guides."),
        ("/talks/", "Recordings, slides and other materials from my public-speaking appearances."),
        ("/bots/", "My fleet of automated accounts."),
    ],
)
def test_list_pages_use_page_specific_metadata_descriptions(client, page, expected_description):
    content = client.get(page).content.decode()

    assert f'<meta name="description" content="{expected_description}" />' in content


@pytest.mark.parametrize(
    ("page", "expected_digest"),
    [
        ("/posts/", "1504b00891fbbd026584b629915c526c35f023d60c058cedeb044849d05d401b"),
        ("/clips/", "16aa691f7161c2aa69d9d104d96e4b31cb5302f3d349b5619899fd7e935d9333"),
        ("/apps/", "ef2af85cce1c663b9422d3b794f35142e7d008977e1e9c2d649208b87296124f"),
        ("/code/", "00e42adbf42c8f4caff7270c01ae0a5efbf87271c64b8f54d7fb9c56c7401557"),
        ("/guides/", "d0ce6e3ca42af59d07b3fa71e04ef5051de41202012b6fdc9b9ac535216b06b3"),
        ("/docs/", "bced3578a4a815d297afebd115ce705f82f366e5807eab902af66ad5f332a5b3"),
        ("/talks/", "6220e551abf42eb39e6233a728ac265bbf0b3a717fe69b956b2f7c0ddaedd0bd"),
        ("/bots/", "9e2991194a5be838f4ff33d1b5403065a752c57e235a28e7253399772dd63b41"),
    ],
)
def test_list_page_visible_text_is_preserved(client, page, expected_digest):
    assert main_text_digest(client.get(page).content.decode()) == expected_digest


@pytest.mark.parametrize("page", ["/posts/", "/clips/", "/apps/", "/code/", "/guides/", "/docs/", "/talks/", "/bots/"])
def test_list_pages_use_semantic_lists(client, page):
    content = client.get(page).content.decode()

    assert '<ul class="catalog-list">' in content
    assert '<li class="row">' in content


def test_catalog_and_chronological_pages_use_heading_hierarchy(client):
    catalog = client.get("/apps/").content.decode()
    chronological = client.get("/posts/").content.decode()

    assert '<h2 class="section-hed twelvecol last">' in catalog
    assert '<h2 class="section-hed twelvecol last">' in chronological
    assert '<div class="section-hed twelvecol last">' not in catalog
    assert '<div class="section-hed twelvecol last">' not in chronological


def test_clip_and_talk_dates_have_machine_readable_values(client):
    clips = [clip for clip in load_clips() if clip.type in {"app", "story"}]
    clip_content = client.get("/clips/").content.decode()
    talk_content = client.get("/talks/").content.decode()

    assert clip_content.count("<time datetime=") == len(clips)
    assert talk_content.count("<time datetime=") == len(load_talks())
    assert all(f'<time datetime="{clip.date:%Y-%m-%d}">' in clip_content for clip in clips)
    assert all(f'<time datetime="{talk.date:%Y-%m-%d}">' in talk_content for talk in load_talks())


def test_talk_detail_page_is_available(client):
    response = client.get("/talks/bare-facts-first-datawrapper/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Bare Facts First" in content
    assert 'rel="author" href="/who-is-ben-welsh/">Ben Welsh</a>' in content
    assert 'src="/static/talks/bare-facts-first-datawrapper/"' in content
    assert "Show the extracted slide text" in content
    assert 'kind="captions" src="/static/talks/bare-facts-first-datawrapper/captions.vtt"' in content
    assert "Show the timestamped transcript" in content
    assert ">Slides PDF<" in content
    assert ">Recording video<" in content
    assert ">Extracted slide text<" in content
    assert ">Timestamped transcript<" in content
    assert ">00:05</time>" in content
    assert ">00:05.160</time>" not in content


def test_talk_detail_page_uses_configured_byline_and_deck_ratio(client):
    content = client.get("/talks/good-trouble-ai/").content.decode()

    assert "Ben Welsh and Scott Klein" in content
    assert 'style="--talk-deck-aspect-ratio: 16 / 9;"' in content
    assert ">Downloads<" in content
    assert "Original sources" not in content


def test_harnessing_ai_talk_page_is_video_only(client):
    response = client.get("/talks/harnessing-ai/")
    talk = next(talk for talk in load_talks() if talk.slug == "harnessing-ai")

    assert response.status_code == 200
    assert talk.slides_url == ""
    content = response.content.decode()
    assert "<h1>Harnessing AI</h1>" in content
    assert 'src="/media/talks/harnessing-ai/video.mp4"' in content
    assert 'poster="/media/talks/harnessing-ai/poster.jpg"' in content
    assert 'aria-labelledby="slides"' not in content


def test_ire_resource_center_talk_page_has_local_deck_and_downloads(client):
    response = client.get("/talks/ire-resource-center/")

    assert response.status_code == 200
    content = response.content.decode()
    assert 'src="/static/talks/ire-resource-center/"' in content
    assert 'style="--talk-deck-aspect-ratio: 48 / 35;"' in content
    assert "Show the extracted slide text" in content
    assert "Semantic search" in content
    assert ">Slides PDF<" in content
    assert 'src="/media/talks/ire-resource-center/video.mp4"' in content
    assert 'poster="/media/talks/ire-resource-center/poster.jpg"' in content
    assert 'kind="captions" src="/static/talks/ire-resource-center/captions.vtt"' in content
    assert "Show the timestamped transcript" in content
    assert "Welcome everybody here." in content
    assert ">Extracted slide text<" in content
    assert ">Recording video<" in content
    assert ">Timestamped transcript<" in content


def test_nicar_ire_resource_center_talk_reuses_the_deck_without_a_recording(client):
    response = client.get("/talks/ire-resource-center-nicar/")

    assert response.status_code == 200
    content = response.content.decode()
    assert 'src="/static/talks/ire-resource-center/"' in content
    assert 'style="--talk-deck-aspect-ratio: 48 / 35;"' in content
    assert "Show the extracted slide text" in content
    assert ">Slides PDF<" in content
    assert ">Extracted slide text<" in content
    assert ">Recording video<" not in content
    assert "Show the timestamped transcript" not in content


def test_storytelling_with_graphics_talk_has_a_local_recording_and_transcript(client):
    response = client.get("/talks/storytelling-with-graphics/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Storytelling with graphics: From raw data to reader impact" in content
    assert 'src="/media/talks/storytelling-with-graphics/video.mp4"' in content
    assert 'poster="/media/talks/storytelling-with-graphics/poster.jpg"' in content
    assert 'kind="captions" src="/static/talks/storytelling-with-graphics/captions.vtt"' in content
    assert "Show the timestamped transcript" in content
    assert "All right. Hello, everybody, and welcome." in content
    assert ">Recording video<" in content
    assert ">Timestamped transcript<" in content
    assert '<h2 id="slides">Slides</h2>' not in content


def test_talk_list_links_to_archived_external_talk_pages(client):
    content = client.get("/talks/").content.decode()

    assert 'href="https://www.poynter.org/shop/reporting-editing/todays-news-for-tomorrow/"' in content
    assert (
        '<a target="_blank" href="https://web.archive.org/web/20260610235645/https://www.poynter.org/shop/reporting-editing/todays-news-for-tomorrow/">“Today’s News For Tomorrow”</a>'
        in content
    )
    assert "Archived page &raquo;" not in content


def test_talk_list_links_to_related_guides(client):
    content = client.get("/talks/").content.decode()

    assert '<a href="https://palewi.re/docs/first-pmtiles-map/">“First PMTiles Map”</a>' in content
    assert "Guide &raquo;" not in content


def test_post_schema_is_a_blog_post_with_a_canonical_main_entity(client):
    post = load_posts()[0]
    canonical_url = f"https://palewi.re{post.get_absolute_url()}"
    content = client.get(post.get_absolute_url()).content.decode()
    json_ld_blocks = [
        json.loads(block)
        for block in re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
            content,
            flags=re.DOTALL,
        )
    ]
    metadata = next(block for block in json_ld_blocks if block["@type"] == "BlogPosting")

    assert metadata["@id"] == canonical_url
    assert metadata["url"] == canonical_url
    assert metadata["mainEntityOfPage"] == {"@type": "WebPage", "@id": canonical_url}
    assert "dateModified" not in metadata


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
