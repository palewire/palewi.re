"""Tests for the django-bakery static site build."""

import json
from html.parser import HTMLParser
from pathlib import Path

from django.core.management import call_command
from django.test import Client, override_settings

from coltrane.content_loaders import load_posts, load_talks

SECURITY_TXT_CONTENT = (
    "Contact: mailto:b@palewi.re\n"
    "Expires: 2027-08-01T00:00:00.000Z\n"
    "Preferred-Languages: en\n"
    "Canonical: https://palewi.re/.well-known/security.txt\n"
)
LLMS_TXT_CONTENT = """# palewi.re

Canonical site: https://palewi.re/
Sitemap: https://palewi.re/sitemap.xml
RSS feed: https://palewi.re/feeds/posts/
JSON Feed: https://palewi.re/feeds/posts.json

Content sections:
- Bio: https://palewi.re/who-is-ben-welsh/
- Posts: https://palewi.re/posts/
- Clips: https://palewi.re/clips/
- Apps: https://palewi.re/apps/
- Code: https://palewi.re/code/
- Guides: https://palewi.re/guides/
- Talks: https://palewi.re/talks/
- Bots: https://palewi.re/bots/

Individual post pages are the canonical primary sources for posts published on this site.
"""


class JsonLdParser(HTMLParser):
    """Collect JSON-LD script bodies from a rendered HTML document."""

    def __init__(self) -> None:
        super().__init__()
        self.blocks: list[str] = []
        self.current_block: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script" and dict(attrs).get("type") == "application/ld+json":
            self.current_block = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.current_block is not None:
            self.blocks.append("".join(self.current_block))
            self.current_block = None

    def handle_data(self, data: str) -> None:
        if self.current_block is not None:
            self.current_block.append(data)


def test_static_build_matches_public_django_pages(tmp_path: Path) -> None:
    """The baked files must retain the public content served by Django."""
    build_dir = tmp_path / "dist"
    with override_settings(BUILD_DIR=str(build_dir)):
        call_command("build")

    client = Client(HTTP_HOST="palewi.re")
    page_paths = [
        "/who-is-ben-welsh/",
        "/posts/",
        "/clips/",
        "/apps/",
        "/code/",
        "/guides/",
        "/docs/",
        "/talks/",
        "/bots/",
        *(post.get_absolute_url() for post in load_posts()),
        *(talk.get_absolute_url() for talk in load_talks() if talk.slug),
    ]

    for page_path in page_paths:
        output_path = build_dir / page_path.strip("/") / "index.html"
        response = client.get(page_path, secure=True)

        assert response.status_code == 200
        assert output_path.read_bytes() == response.content

    generated_resources = {
        "/feeds/posts/": "feeds/posts/index.xml",
        "/feeds/posts.json": "feeds/posts.json",
        "/robots.txt": "robots.txt",
        "/llms.txt": "llms.txt",
        "/sitemap.xml": "sitemap.xml",
        "/sitemap-static.xml": "sitemap-static.xml",
        "/sitemap-posts.xml": "sitemap-posts.xml",
    }
    for page_path, output_path in generated_resources.items():
        response = client.get(page_path, secure=True)

        assert response.status_code == 200
        assert (build_dir / output_path).read_bytes() == response.content

    not_found = client.get("/this-page-does-not-exist/", secure=True)
    assert not_found.status_code == 404
    assert (build_dir / "404.html").read_bytes() == not_found.content

    assert (build_dir / "500.html").is_file()
    assert (build_dir / "favicon.ico").is_file()
    assert (build_dir / "static/styles.css").is_file()
    assert len(list(build_dir.glob("posts/*/*/*/*/index.html"))) == len(load_posts())
    assert not (build_dir / "posts/2008/05/18/bill-oreilly-flips-out-the-ringtone/index.html").exists()
    assert not (build_dir / "posts/2010/03/10/google-charts-takes-tufte-challenge/index.html").exists()


def test_security_txt_is_baked_as_canonical_plain_text(tmp_path: Path) -> None:
    """The security contact document remains a direct plain-text static asset."""
    build_dir = tmp_path / "dist"
    with override_settings(BUILD_DIR=str(build_dir)):
        call_command("build")

    response = Client(HTTP_HOST="palewi.re").get("/.well-known/security.txt", secure=True)

    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain; charset=utf-8"
    assert not response.has_header("Location")
    assert response.content.decode() == SECURITY_TXT_CONTENT
    assert build_dir.joinpath(".well-known/security.txt").read_text(encoding="utf-8") == SECURITY_TXT_CONTENT


def test_llms_txt_is_baked_as_canonical_plain_text(tmp_path: Path) -> None:
    """The reader guide remains a direct plain-text static asset."""
    build_dir = tmp_path / "dist"
    with override_settings(BUILD_DIR=str(build_dir)):
        call_command("build")

    response = Client(HTTP_HOST="palewi.re").get("/llms.txt", secure=True)

    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain; charset=utf-8"
    assert not response.has_header("Location")
    assert response.content.decode() == LLMS_TXT_CONTENT
    assert build_dir.joinpath("llms.txt").read_text(encoding="utf-8") == LLMS_TXT_CONTENT


def test_every_baked_json_ld_block_is_valid_json(tmp_path: Path) -> None:
    """Structured data stays parseable as content changes."""
    build_dir = tmp_path / "dist"
    with override_settings(BUILD_DIR=str(build_dir)):
        call_command("build")

    for page_path in build_dir.rglob("*.html"):
        parser = JsonLdParser()
        parser.feed(page_path.read_text(encoding="utf-8"))
        parser.close()
        for block in parser.blocks:
            assert json.loads(block), page_path.relative_to(build_dir)
