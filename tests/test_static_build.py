"""Tests for the django-bakery static site build."""

from pathlib import Path

from django.core.management import call_command
from django.test import Client, override_settings

from coltrane.content_loaders import load_posts


def test_static_build_matches_public_django_pages(tmp_path: Path) -> None:
    """The baked files must retain the public content served by Django."""
    build_dir = tmp_path / "dist"
    with override_settings(BUILD_DIR=str(build_dir)):
        call_command("build")

    client = Client(HTTP_HOST="palewi.re")
    page_paths = [
        "/who-is-ben-welsh/",
        "/work/",
        "/talks/",
        "/posts/",
        "/docs/",
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
