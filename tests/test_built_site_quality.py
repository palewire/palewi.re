"""Tests for offline checks over django-bakery output."""

from __future__ import annotations

from pathlib import Path
from shutil import copytree

import pytest
from click.testing import CliRunner

from scripts.check_built_site import check_built_site, cli

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "built_site_quality" / "valid"


@pytest.fixture
def build_dir(tmp_path: Path) -> Path:
    destination = tmp_path / "dist"
    copytree(FIXTURE_DIR, destination)
    return destination


def write_page(build_dir: Path, relative_path: str, content: str) -> None:
    path = build_dir / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_valid_built_site_passes(build_dir: Path) -> None:
    assert check_built_site(build_dir) == []

    result = CliRunner().invoke(cli, ["--build-dir", str(build_dir)])

    assert result.exit_code == 0
    assert "passed" in result.output


def test_cli_accepts_only_exact_baseline_fingerprints(build_dir: Path, tmp_path: Path) -> None:
    write_page(build_dir, "docs/index.html", '<a href="/missing/">Missing page</a>')
    baseline = tmp_path / "baseline.txt"
    baseline.write_text(
        check_built_site(build_dir)[0].fingerprint() + "\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(cli, ["--build-dir", str(build_dir), "--baseline", str(baseline)])

    assert result.exit_code == 0
    assert "1 documented existing issue" in result.output

    write_page(build_dir, "docs/index.html", '<a href="/another-missing/">Another missing page</a>')
    result = CliRunner().invoke(cli, ["--build-dir", str(build_dir), "--baseline", str(baseline)])

    assert result.exit_code == 1
    assert "another-missing" in result.output


def test_cli_rejects_findings_that_exceed_baseline_count(build_dir: Path, tmp_path: Path) -> None:
    write_page(
        build_dir,
        "docs/index.html",
        '<a href="/missing/">First missing page</a><a href="/missing/">Second missing page</a>',
    )
    baseline = tmp_path / "baseline.txt"
    baseline.write_text(
        check_built_site(build_dir)[0].fingerprint() + "\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(cli, ["--build-dir", str(build_dir), "--baseline", str(baseline)])

    assert result.exit_code == 1
    assert "1 new built-site quality issue" in result.output
    assert "missing/" in result.output


@pytest.mark.parametrize(
    ("relative_path", "content", "code"),
    [
        (
            "docs/index.html",
            '<a href="/missing/">Missing page</a>',
            "missing-generated-page",
        ),
        (
            "docs/index.html",
            '<img src="/static/missing.png" alt="Missing asset">',
            "missing-local-asset",
        ),
        (
            "docs/index.html",
            '<img src="/static/logo.png" alt="">',
            "image-alt",
        ),
        (
            "docs/index.html",
            '<a href="https:///missing-host">Broken external URL</a>',
            "invalid-external-url",
        ),
        (
            "docs/index.html",
            '<a href="https://[broken">Broken external URL</a>',
            "invalid-external-url",
        ),
    ],
)
def test_checker_reports_invalid_html_references(build_dir: Path, relative_path: str, content: str, code: str) -> None:
    write_page(build_dir, relative_path, content)

    findings = check_built_site(build_dir)

    assert [finding.code for finding in findings] == [code]
    assert findings[0].source == relative_path


def test_checker_allows_exact_worker_routes_without_allowing_unknown_paths(build_dir: Path) -> None:
    write_page(
        build_dir,
        "docs/index.html",
        """
        <a href="/">Home</a>
        <a href="/docs/first-python-notebook/">Notebook</a>
        <a href="/colophon/">Colophon</a>
        <a href="/applications/twitter-style-infinite-scroll-with-django-demo/">Demo</a>
        <a href="/docs/not-a-real-doc/">Missing documentation</a>
        <a href="/not-a-real-legacy-route/">Missing legacy route</a>
        """,
    )

    findings = check_built_site(build_dir)

    assert [finding.code for finding in findings] == ["missing-generated-page", "missing-generated-page"]
    assert [finding.message.rsplit(" ", maxsplit=1)[-1] for finding in findings] == [
        "/docs/not-a-real-doc/",
        "/not-a-real-legacy-route/",
    ]


def test_checker_allows_explicitly_decorative_image(build_dir: Path) -> None:
    write_page(build_dir, "docs/index.html", '<img src="/static/logo.png" alt="" role="presentation">')

    assert check_built_site(build_dir) == []


def test_checker_reports_duplicate_canonical_url(build_dir: Path) -> None:
    write_page(
        build_dir,
        "work/index.html",
        '<link rel="canonical" href="https://palewi.re/docs/">',
    )

    findings = check_built_site(build_dir)

    assert [finding.code for finding in findings] == ["duplicate-canonical"]
    assert "docs/index.html, work/index.html" in findings[0].source


@pytest.mark.parametrize(
    ("relative_path", "content", "code"),
    [
        ("sitemap-posts.xml", "<?xml version='1.0'?><urlset></urlset>", "missing-sitemap-post"),
        ("feeds/posts/index.xml", "<?xml version='1.0'?><rss><channel></channel></rss>", "missing-feed-post"),
    ],
)
def test_checker_reports_missing_post_coverage(build_dir: Path, relative_path: str, content: str, code: str) -> None:
    write_page(build_dir, relative_path, content)

    findings = check_built_site(build_dir)

    assert [finding.code for finding in findings] == [code]
