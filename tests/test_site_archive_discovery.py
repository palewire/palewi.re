"""Offline tests for public-page discovery."""

from pathlib import Path

import pytest
import requests

from coltrane.content_loaders import Doc
from scripts.site_archive import discovery
from scripts.site_archive.discovery import ORIGIN, PageDiscovery, build_seeds, is_page_url, normalize_url
from scripts.site_archive.manifest import ArchiveError, Manifest, ManifestStore


def response(body: str = "", status: int = 200, content_type: str = "text/html") -> requests.Response:
    """Construct an in-memory HTTP response.

    Args:
        body: Response text.
        status: HTTP status.
        content_type: Response MIME type.

    Returns:
        A fully buffered requests response.

    Examples:
        ``response("<p>Hello</p>")`` creates an HTML response.
    """
    result = requests.Response()
    result.status_code = status
    result._content = body.encode()
    result._content_consumed = True
    result.headers["Content-Type"] = content_type
    result.encoding = "utf-8"
    return result


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("/posts/#latest", f"{ORIGIN}/posts/"),
        ("http://www.palewi.re/docs/x/index.html", f"{ORIGIN}/docs/x/index.html"),
        ("next.html", f"{ORIGIN}/docs/next.html"),
        ("https://example.com/", None),
        ("https://mastodon.palewi.re/", None),
        ("/search.html?q=foo", None),
        ("mailto:ben@example.com", None),
        ("https://user:pass@palewi.re/posts/", None),
        ("https://palewi.re:8080/posts/", None),
        ("https://[broken/", None),
        ("/%2e%2e/private", None),
        ("/docs/%5cother", None),
        ("/docs/%2fother", None),
        ("/docs/space here", None),
    ],
)
def test_normalize_url(value: str, expected: str | None) -> None:
    """Check URL scope and normalization.

    Args:
        value: Candidate link.
        expected: Expected normalized URL or rejection.

    Returns:
        None.

    Examples:
        Parametrized cases cover aliases, fragments, and excluded hosts.
    """
    assert normalize_url(value, f"{ORIGIN}/docs/") == expected


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/posts/", True),
        ("/posts/page/2/", True),
        ("/docs/guide/chapter.html", True),
        ("/static/talks/deck/", True),
        ("/static/talks/deck/file.pdf", False),
        ("/docs/guide/_static/example.html", False),
        ("/static/index.html", False),
        ("/health/", False),
        ("/media/video", False),
        ("/feeds/posts/", False),
        ("/", False),
        ("/404.html", False),
        ("/search.html", False),
    ],
)
def test_page_filter(path: str, expected: bool) -> None:
    """Check page eligibility.

    Args:
        path: Public path.
        expected: Whether it is a page candidate.

    Returns:
        None.

    Examples:
        HTML decks are included while media files are excluded.
    """
    assert is_page_url(f"{ORIGIN}{path}") is expected


def test_build_seeds_include_talks_decks_and_docs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Include pages missing from the site's sitemap.

    Args:
        tmp_path: Temporary build directory.
        monkeypatch: Patches the docs catalog.

    Returns:
        None.

    Examples:
        Stable deck entrypoints are included; hashed copies are not.
    """
    for name in [
        "posts/2026/01/01/example/index.html",
        "talks/example/index.html",
        "static/talks/example/index.html",
        "static/talks/example/index.aabbcc.html",
        "static/ignored.html",
        "404.html",
        "500.html",
    ]:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("<p>Page</p>")
    monkeypatch.setattr(
        discovery,
        "load_docs",
        lambda: [
            Doc("Guide", "lesson-plan", f"{ORIGIN}/docs/guide/"),
            Doc("External", "software", "https://example.com/"),
        ],
    )
    assert build_seeds(tmp_path) == [
        f"{ORIGIN}/docs/guide/",
        f"{ORIGIN}/docs/guide/sitemap.xml",
        f"{ORIGIN}/posts/2026/01/01/example/",
        f"{ORIGIN}/sitemap.xml",
        f"{ORIGIN}/static/talks/example/",
        f"{ORIGIN}/talks/example/",
    ]


def test_empty_or_missing_build_is_an_error(tmp_path: Path) -> None:
    """Reject an inventory with no build input.

    Args:
        tmp_path: Empty directory.

    Returns:
        None.

    Examples:
        A missing dist directory instructs the user to run make bake.
    """
    for path in [tmp_path, tmp_path / "absent"]:
        with pytest.raises(ArchiveError, match="make bake"):
            build_seeds(path)


def test_discovery_resumes_links_and_sitemaps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Checkpoint discovery and avoid link cycles or off-site requests.

    Args:
        tmp_path: Manifest directory.
        monkeypatch: Replaces network access.

    Returns:
        None.

    Examples:
        The second batch processes the first batch's remaining queue.
    """
    first = f"{ORIGIN}/docs/guide/"
    second = f"{ORIGIN}/docs/guide/next.html"
    sitemap = f"{ORIGIN}/sitemap.xml"
    responses = {
        first: response('<a href="next.html">Next</a><a href="https://example.com/">Away</a>'),
        second: response('<a href="./">Back</a><a href="/posts/page/2/">Older</a>'),
        sitemap: response(
            "<sitemapindex><sitemap><loc>https://palewi.re/sitemap-posts.xml</loc></sitemap></sitemapindex>",
            content_type="application/xml",
        ),
        f"{ORIGIN}/sitemap-posts.xml": response(
            "<urlset><url><loc>https://palewi.re/posts/page/2/</loc></url>"
            "<url><loc>https://example.com/</loc></url></urlset>",
            content_type="text/xml",
        ),
        f"{ORIGIN}/posts/page/2/": response("Done"),
    }
    visited: list[str] = []

    def get(_session: requests.Session, url: str, **kwargs: object) -> requests.Response:
        """Return a fixture response.

        Args:
            _session: Unused session.
            url: Requested URL.
            **kwargs: Request options.

        Returns:
            Fixture response.

        Examples:
            Used in place of Session.get.
        """
        assert kwargs["allow_redirects"] is False
        visited.append(url)
        return responses[url]

    monkeypatch.setattr(requests.Session, "get", get)
    store = ManifestStore(tmp_path / "manifest.json")
    state = Manifest()
    assert PageDiscovery(state, store, delay=0).run([first, sitemap], limit=1) == 1
    state = store.load()
    assert state.discovery_queue == [sitemap, second]
    assert state.pages[first].live_status == "live"
    assert not state.discovery_complete
    PageDiscovery(state, store, delay=0).run([first, sitemap], limit=10)
    assert state.discovery_complete
    assert len(visited) == len(set(visited)) == 5
    assert len(state.pages) == 3


@pytest.mark.parametrize("status", [404, 410, 403])
def test_missing_sitemap_does_not_stop_public_navigation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    """Record unavailable sitemaps while continuing to read public links.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces network calls.
        status: Unavailable sitemap HTTP status.

    Returns:
        None.

    Examples:
        A 403 sitemap is recorded without retrying through access controls.
    """
    sitemap = f"{ORIGIN}/docs/guide/sitemap.xml"
    root = f"{ORIGIN}/docs/guide/"
    monkeypatch.setattr(
        requests.Session,
        "get",
        lambda _self, url, **kwargs: response(status=status) if url == sitemap else response("Public page"),
    )
    state = Manifest()
    PageDiscovery(state, ManifestStore(tmp_path / "state.json"), delay=0).run([sitemap, root])
    assert sitemap in state.discovery_errors
    assert state.pages[root].live_status == "live"
    assert not state.discovery_complete


@pytest.mark.parametrize("destination", ["https://example.com/", "/posts/", "/alias/"])
def test_redirects_are_not_captured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, destination: str) -> None:
    """Follow only same-host destinations and detect self redirects.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces network calls.
        destination: Redirect target.

    Returns:
        None.

    Examples:
        An off-site redirect is recorded but never fetched.
    """
    result = response(status=302)
    result.headers["Location"] = destination
    monkeypatch.setattr(requests.Session, "get", lambda *args, **kwargs: result)
    state = Manifest()
    alias = f"{ORIGIN}/alias/"
    PageDiscovery(state, ManifestStore(tmp_path / "state.json"), delay=0).run([alias], limit=1)
    if destination == "/alias/":
        assert state.pages[alias].live_status == "error"
        assert "redirect cycle" in state.discovery_errors[alias]
    else:
        assert state.pages[alias].live_status == "redirect"
        assert state.discovery_queue == ([f"{ORIGIN}/posts/"] if destination == "/posts/" else [])


def test_errors_preserve_existing_pages(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep earlier page records when a later discovery request fails.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces network calls.

    Returns:
        None.

    Examples:
        A timeout must not delete previously discovered URLs.
    """
    state = Manifest()
    url = f"{ORIGIN}/posts/"
    state.page(url).live_status = "live"

    def fail(*args: object, **kwargs: object) -> requests.Response:
        """Raise a fake timeout.

        Args:
            *args: Unused positional arguments.
            **kwargs: Unused options.

        Returns:
            Never returns.

        Examples:
            Replaces a network request in this test.
        """
        raise requests.Timeout("Timed out")

    monkeypatch.setattr(requests.Session, "get", fail)
    store = ManifestStore(tmp_path / "state.json")
    PageDiscovery(state, store, delay=0).run([])
    assert store.load().pages[url].live_status == "error"
    assert state.discovery_errors[url] == "Timed out"
    assert not state.discovery_complete


@pytest.mark.parametrize(
    ("result", "message"),
    [
        (response(status=302), "no Location"),
        (response("binary", content_type="image/png"), "expected HTML"),
        (response("<broken", content_type="text/xml"), "malformed sitemap"),
        (response("<not-sitemap/>", content_type="text/xml"), "expected a sitemap"),
    ],
)
def test_invalid_responses_are_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, result: requests.Response, message: str
) -> None:
    """Record invalid responses as errors instead of valid pages.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces network calls.
        result: Invalid response.
        message: Expected error text.

    Returns:
        None.

    Examples:
        An image response cannot count as a live HTML page.
    """
    monkeypatch.setattr(requests.Session, "get", lambda *args, **kwargs: result)
    url = f"{ORIGIN}/sitemap.xml" if result.headers["Content-Type"] == "text/xml" else f"{ORIGIN}/page/"
    state = Manifest()
    PageDiscovery(state, ManifestStore(tmp_path / "state.json"), delay=0).run([url])
    assert message in state.discovery_errors[url]


def test_response_size_limit_and_deadline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Stop large responses and retain unprocessed URLs when time runs out.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces network access and size limit.

    Returns:
        None.

    Examples:
        A deadline before now performs no network requests.
    """
    monkeypatch.setattr(discovery, "MAX_RESPONSE_BYTES", 2)
    monkeypatch.setattr(requests.Session, "get", lambda *args, **kwargs: response("large"))
    store = ManifestStore(tmp_path / "state.json")
    state = Manifest()
    url = f"{ORIGIN}/page/"
    assert PageDiscovery(state, store, delay=0).run([url], deadline=0) == 0
    assert store.load().discovery_queue == [url]
    PageDiscovery(state, store, delay=0).run([url], limit=1)
    assert "exceeds" in state.discovery_errors[url]


def test_non_html_page_and_fake_sitemap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject responses whose format does not match their inventory role.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces network access.

    Returns:
        None.

    Examples:
        An HTML error page at sitemap.xml is not a successful sitemap.
    """
    root = f"{ORIGIN}/page/"
    sitemap = f"{ORIGIN}/sitemap.xml"
    monkeypatch.setattr(
        requests.Session,
        "get",
        lambda _self, url, **kwargs: (
            response("<urlset/>", content_type="application/xml") if url == root else response("Not a sitemap")
        ),
    )
    state = Manifest()
    PageDiscovery(state, ManifestStore(tmp_path / "state.json"), delay=0).run([root, sitemap])
    assert "received XML" in state.discovery_errors[root]
    assert "received HTML" in state.discovery_errors[sitemap]


def test_redirect_cycle_across_pages(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep a multi-page redirect loop out of confirmed live pages.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces network access.

    Returns:
        None.

    Examples:
        A to B to A terminates with a recorded discovery error.
    """
    first = f"{ORIGIN}/first/"
    second = f"{ORIGIN}/second/"

    def get(_session: requests.Session, url: str, **kwargs: object) -> requests.Response:
        """Return the next redirect in the loop.

        Args:
            _session: Unused session.
            url: Requested page.
            **kwargs: Unused request options.

        Returns:
            A redirect to the other page.

        Examples:
            The first page redirects to the second.
        """
        result = response(status=301)
        result.headers["Location"] = second if url == first else first
        return result

    monkeypatch.setattr(requests.Session, "get", get)
    state = Manifest()
    PageDiscovery(state, ManifestStore(tmp_path / "state.json"), delay=0).run([first])
    assert "redirect cycle" in state.discovery_errors[second]
    assert not state.discovery_queue


def test_live_missing_and_completed_sweep_restart(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Retain missing pages and revisit them in the next sweep.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces network access.

    Returns:
        None.

    Examples:
        A page returning 404 is not silently erased from the inventory.
    """
    url = f"{ORIGIN}/page/"
    state = Manifest()
    store = ManifestStore(tmp_path / "state.json")
    monkeypatch.setattr(requests.Session, "get", lambda *args, **kwargs: response(status=404))
    PageDiscovery(state, store, delay=0).run([url])
    assert state.pages[url].live_status == "missing"
    monkeypatch.setattr(requests.Session, "get", lambda *args, **kwargs: response("Recovered"))
    PageDiscovery(state, store, delay=0).run([])
    assert state.pages[url].live_status == "live"
    assert state.discovery_complete


@pytest.mark.parametrize("status", [429, 503])
def test_service_failures_defer_remaining_discovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    """Stop requesting pages from a throttled or unavailable server.

    Args:
        tmp_path: State directory.
        monkeypatch: Replaces network access.
        status: Temporary server failure.

    Returns:
        None.

    Examples:
        A 429 response leaves both pages queued for a future run.
    """
    first = f"{ORIGIN}/first/"
    second = f"{ORIGIN}/second/"
    monkeypatch.setattr(requests.Session, "get", lambda *args, **kwargs: response(status=status))
    state = Manifest()
    attempted = PageDiscovery(state, ManifestStore(tmp_path / "state.json"), delay=0).run([first, second])
    assert attempted == 1
    assert state.discovery_queue == [second, first]
    assert not state.discovery_seen
