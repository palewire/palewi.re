"""Discover public HTML pages without crawling outside palewi.re."""

from __future__ import annotations

import time
import xml.etree.ElementTree as ElementTree
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

import requests

from coltrane.content_loaders import load_docs
from scripts.check_built_site import ERROR_PAGES, PageParser, public_url_for_page
from scripts.site_archive.manifest import ArchiveError, Manifest, ManifestStore, utc_now

ORIGIN = "https://palewi.re"
USER_AGENT = "palewi.re archive inventory (https://github.com/palewire/palewi.re)"
MAX_RESPONSE_BYTES = 5_000_000


def normalize_url(value: str, base: str = f"{ORIGIN}/") -> str | None:
    """Resolve a public same-site URL, excluding queries and unsafe paths.

    Args:
        value: Absolute URL or relative link.
        base: Public page against which to resolve relative links.

    Returns:
        An HTTPS URL without a fragment, or None for an excluded link.

    Examples:
        >>> normalize_url("/posts/#latest")
        'https://palewi.re/posts/'
    """
    try:
        parsed = urlsplit(urljoin(base, value))
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname not in {"palewi.re", "www.palewi.re"}
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 80 if parsed.scheme == "http" else 443}
        or parsed.query
        or any(character.isspace() or ord(character) < 32 for character in value)
    ):
        return None
    path = parsed.path or "/"
    decoded = unquote(path)
    if "\\" in decoded or "//" in decoded or any(part in {".", ".."} for part in decoded.split("/")):
        return None
    return urlunsplit(("https", "palewi.re", path, "", ""))


def is_page_url(url: str) -> bool:
    """Distinguish public page links from downloads and operational endpoints.

    Args:
        url: Normalized public URL.

    Returns:
        Whether this URL is eligible for an HTML page check.

    Examples:
        >>> is_page_url("https://palewi.re/posts/")
        True
    """
    path = urlsplit(url).path
    if path in {"/", "/health/", "/404.html", "/500.html", "/search.html"}:
        return False
    if path.startswith(("/.well-known/", "/media/", "/feeds/")):
        return False
    if path.startswith("/static/") and not path.startswith("/static/talks/"):
        return False
    if any(part in {"_sources", "_static", "_downloads", "_app", "node_modules"} for part in path.split("/")):
        return False
    return Path(path).suffix.lower() in {"", ".html", ".htm"}


def build_seeds(build_dir: Path) -> list[str]:
    """Enumerate built pages and same-site documentation entrypoints.

    Args:
        build_dir: Existing Django Bakery output directory.

    Returns:
        Sorted unique expected pages and sitemap URLs.

    Raises:
        ArchiveError: The build is absent or contains no public HTML pages.

    Examples:
        Call ``build_seeds(Path("dist"))`` after ``make bake``.
    """
    if not build_dir.is_dir():
        raise ArchiveError(f"{build_dir}: build directory is missing; run make bake")
    urls: set[str] = set()
    for path in build_dir.rglob("*.html"):
        if path.name in ERROR_PAGES:
            continue
        relative = path.relative_to(build_dir).as_posix()
        if relative.startswith("static/") and (not relative.startswith("static/talks/") or path.name != "index.html"):
            continue
        url = normalize_url(public_url_for_page(path, build_dir))
        if url and is_page_url(url):
            urls.add(url)
    if not urls:
        raise ArchiveError(f"{build_dir}: no public HTML pages found; run make bake")
    for doc in load_docs():
        url = normalize_url(doc.url)
        if url and is_page_url(url):
            urls.add(url)
            urls.add(urljoin(url, "sitemap.xml"))
    urls.add(f"{ORIGIN}/sitemap.xml")
    return sorted(urls)


class PageDiscovery:
    """Traverse public pages and sitemaps with a persistent work queue."""

    def __init__(self, manifest: Manifest, store: ManifestStore, *, timeout: float = 15, delay: float = 0.25):
        """Configure one discovery run.

        Args:
            manifest: Mutable archive state.
            store: Store used to checkpoint each result.
            timeout: Per-request network timeout in seconds.
            delay: Pause between requests in seconds.

        Returns:
            None.

        Examples:
            Use ``PageDiscovery(manifest, store).run(seeds, limit=100)``.
        """
        self.manifest = manifest
        self.store = store
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT

    def enqueue(self, url: str) -> None:
        """Queue a URL once during this discovery sweep.

        Args:
            url: Normalized same-site page or sitemap URL.

        Returns:
            None.

        Examples:
            ``discovery.enqueue("https://palewi.re/posts/")`` queues posts.
        """
        if url not in self.manifest.discovery_seen and url not in self.manifest.discovery_queue:
            self.manifest.discovery_queue.append(url)
            self.manifest.discovery_complete = False
        if is_page_url(url):
            self.manifest.page(url)

    def run(self, seeds: list[str], *, limit: int = 100, deadline: float = float("inf")) -> int:
        """Process a limited batch, retaining unfinished and failed work.

        Args:
            seeds: Expected build pages and public sitemap entrypoints.
            limit: Maximum URLs to fetch.
            deadline: Stop starting requests at this monotonic clock value.

        Returns:
            Number of URLs attempted.

        Examples:
            ``discovery.run(seeds, limit=10)`` handles at most ten URLs.
        """
        if not self.manifest.discovery_queue:
            self.manifest.discovery_seen = []
            self.manifest.discovery_errors = {}
            self.manifest.discovery_started_at = utc_now()
            # Revisit old pages too: a temporarily absent link must not erase them.
            seeds = list(dict.fromkeys([*seeds, *self.manifest.pages]))
        self.manifest.discovery_complete = False
        for url in seeds:
            self.enqueue(url)
        attempted = 0
        try:
            while self.manifest.discovery_queue and attempted < limit and time.monotonic() < deadline:
                url = self.manifest.discovery_queue[0]
                defer = False
                try:
                    self.visit(url)
                except (requests.RequestException, ArchiveError) as error:
                    self.manifest.discovery_errors[url] = str(error)
                    defer = isinstance(error, (requests.ConnectionError, requests.Timeout)) or (
                        isinstance(error, requests.HTTPError)
                        and error.response is not None
                        and error.response.status_code in {429, 502, 503, 504}
                    )
                    if is_page_url(url):
                        page = self.manifest.page(url)
                        page.live_status = "error"
                        page.live_checked_at = utc_now()
                        page.live_error = str(error)
                self.manifest.discovery_queue.pop(0)
                if defer:
                    self.manifest.discovery_queue.append(url)
                else:
                    self.manifest.discovery_seen.append(url)
                attempted += 1
                self.manifest.discovery_complete = (
                    not self.manifest.discovery_queue and not self.manifest.discovery_errors
                )
                self.store.save(self.manifest)
                if defer:
                    break
                if self.manifest.discovery_queue and attempted < limit and time.monotonic() < deadline:
                    time.sleep(self.delay)
        finally:
            self.session.close()
            self.store.save(self.manifest)
        return attempted

    def visit(self, url: str) -> None:
        """Read one page without automatically following redirects.

        Args:
            url: Same-site URL selected from the queue.

        Returns:
            None. Updates page status and queues discovered links.

        Raises:
            ArchiveError: A response is invalid or too large.
            requests.RequestException: The request fails.

        Examples:
            ``discovery.visit("https://palewi.re/posts/")`` reads its links.
        """
        page = self.manifest.page(url) if is_page_url(url) else None
        if page:
            page.live_checked_at = utc_now()
            page.live_error = ""
        with self.session.get(url, timeout=self.timeout, allow_redirects=False, stream=True) as response:
            if response.status_code in {301, 302, 303, 307, 308}:
                if page:
                    page.live_status = "redirect"
                destination = normalize_url(response.headers.get("Location", ""), url)
                if not response.headers.get("Location"):
                    raise ArchiveError(f"{url}: redirect has no Location")
                if destination == url or destination in self.manifest.discovery_seen:
                    if destination == url or (
                        destination in self.manifest.pages
                        and self.manifest.pages[destination].live_status == "redirect"
                    ):
                        raise ArchiveError(f"{url}: redirect cycle")
                if destination and (is_page_url(destination) or destination.endswith(".xml")):
                    self.enqueue(destination)
                return
            if response.status_code in {404, 410} or (response.status_code == 403 and url.endswith("/sitemap.xml")):
                if page:
                    page.live_status = "missing"
                    page.live_error = f"Live page returned HTTP {response.status_code}"
                self.manifest.discovery_errors[url] = f"HTTP {response.status_code}"
                self.manifest.discovery_complete = False
                return
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
            if content_type not in {"text/html", "application/xhtml+xml", "application/xml", "text/xml"}:
                raise ArchiveError(f"{url}: expected HTML or sitemap XML, got {content_type!r}")
            body = bytearray()
            for chunk in response.iter_content(chunk_size=64_000):
                body.extend(chunk)
                if len(body) > MAX_RESPONSE_BYTES:
                    raise ArchiveError(f"{url}: response exceeds {MAX_RESPONSE_BYTES} bytes")
            if content_type in {"application/xml", "text/xml"}:
                if page:
                    raise ArchiveError(f"{url}: expected an HTML page, received XML")
                self.read_sitemap(bytes(body), url)
            else:
                if not page:
                    raise ArchiveError(f"{url}: expected a sitemap, received HTML")
                page.live_status = "live"
                parser = PageParser()
                parser.feed(bytes(body).decode(response.encoding or "utf-8", errors="replace"))
                for link in parser.links:
                    destination = normalize_url(link.value, url)
                    if link.tag == "a" and destination and is_page_url(destination):
                        self.enqueue(destination)
            self.manifest.discovery_errors.pop(url, None)

    def read_sitemap(self, body: bytes, url: str) -> None:
        """Read a sitemap index or URL set without visiting off-site entries.

        Args:
            body: Downloaded XML bytes.
            url: Source sitemap URL.

        Returns:
            None. Adds same-site entries to the discovery queue.

        Raises:
            ArchiveError: XML is malformed or not a sitemap.

        Examples:
            ``discovery.read_sitemap(xml_bytes, sitemap_url)`` queues its URLs.
        """
        try:
            root = ElementTree.fromstring(body)
        except ElementTree.ParseError as error:
            raise ArchiveError(f"{url}: malformed sitemap: {error}") from error
        kind = root.tag.rsplit("}", 1)[-1]
        if kind not in {"sitemapindex", "urlset"}:
            raise ArchiveError(f"{url}: expected a sitemap index or URL set")
        for element in root.iter():
            if element.tag.rsplit("}", 1)[-1] != "loc" or not element.text:
                continue
            destination = normalize_url(element.text.strip(), url)
            if destination and (is_page_url(destination) or kind == "sitemapindex"):
                self.enqueue(destination)
