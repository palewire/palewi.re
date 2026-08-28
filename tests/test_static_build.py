"""Tests for the django-bakery static site build."""

from pathlib import Path

from django.core.management import call_command
from django.test import Client, override_settings

from coltrane.content_loaders import load_posts

SECURITY_TXT_CONTENT = (
    "Contact: mailto:b@palewi.re\n"
    "Expires: 2027-08-01T00:00:00.000Z\n"
    "Preferred-Languages: en\n"
    "Canonical: https://palewi.re/.well-known/security.txt\n"
)


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
    ]

    for page_path in page_paths:
        output_path = build_dir / page_path.strip("/") / "index.html"
        response = client.get(page_path, secure=True)

        assert response.status_code == 200
        assert output_path.read_bytes() == response.content

    for page_path in ["/feeds/posts/", "/robots.txt", "/sitemap.xml", "/sitemap-static.xml", "/sitemap-posts.xml"]:
        output_path = build_dir / ("feeds/posts/index.xml" if page_path == "/feeds/posts/" else page_path.strip("/"))
        response = client.get(page_path, secure=True)

        assert response.status_code == 200
        assert output_path.read_bytes() == response.content

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
