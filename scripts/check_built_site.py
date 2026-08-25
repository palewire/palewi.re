"""Validate links, metadata, and post coverage in a baked static site."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ElementTree
from collections import defaultdict
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import SplitResult, unquote, urljoin, urlsplit

import click

PUBLIC_HOSTS = frozenset({"palewi.re", "www.palewi.re"})
ERROR_PAGES = frozenset({"404.html", "500.html"})
FEED_POST_LIMIT = 10
POST_PATH_PATTERN = re.compile(r"^/posts/(\d{4}/\d{2}/\d{2}/[^/]+)/$")
HOSTNAME_WITHOUT_SCHEME = re.compile(r"^(?:www\.)?[\w-]+(?:\.[\w-]+)+/")
DEFAULT_BASELINE_PATH = Path(__file__).with_name("built_site_quality_baseline.txt")


@dataclass(frozen=True)
class Finding:
    """One actionable quality issue in a generated file."""

    code: str
    source: str
    message: str

    def format(self) -> str:
        """Render a concise, stable terminal message."""
        return f"{self.code.upper()}  {self.source}  {self.message}"

    def fingerprint(self) -> str:
        """Return the stable key used to acknowledge existing quality debt."""
        return "\t".join((self.code, self.source, self.message))


@dataclass(frozen=True)
class Link:
    """One URL-bearing HTML attribute."""

    tag: str
    attribute: str
    value: str


class PageParser(HTMLParser):
    """Collect the small subset of HTML metadata this checker validates."""

    def __init__(self) -> None:
        super().__init__()
        self.canonicals: list[str] = []
        self.links: list[Link] = []
        self.image_issues: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name.lower(): value for name, value in attrs}
        if tag == "link" and "canonical" in (attributes.get("rel") or "").lower().split():
            canonical = attributes.get("href")
            if canonical:
                self.canonicals.append(canonical)

        for attribute in ("href", "src"):
            value = attributes.get(attribute)
            if value:
                self.links.append(Link(tag=tag, attribute=attribute, value=value))

        if tag == "img":
            alt = attributes.get("alt")
            role = (attributes.get("role") or "").lower()
            if alt is None:
                self.image_issues.append("image is missing an alt attribute")
            elif not alt.strip() and role not in {"presentation", "none"}:
                self.image_issues.append(
                    'image has empty alt text; use descriptive text or mark a decorative image with role="presentation"'
                )


def build_urls(build_dir: Path) -> set[str]:
    """Return public URL paths represented by files in a static build."""
    urls: set[str] = set()
    for path in build_dir.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(build_dir).as_posix()
        urls.add(f"/{relative}")
        if relative.endswith("/index.html"):
            directory = relative.removesuffix("/index.html")
            urls.update({f"/{directory}/", f"/{directory}"})
        elif relative == "index.html":
            urls.update({"/", ""})
        elif relative.endswith("/index.xml"):
            directory = relative.removesuffix("/index.xml")
            urls.update({f"/{directory}/", f"/{directory}"})
    return urls


def public_url_for_page(path: Path, build_dir: Path) -> str:
    """Return the URL path corresponding to one generated HTML page."""
    relative = path.relative_to(build_dir).as_posix()
    if relative == "index.html":
        return "/"
    if relative.endswith("/index.html"):
        return f"/{relative.removesuffix('index.html')}"
    return f"/{relative}"


def is_internal_url(parsed: SplitResult) -> bool:
    """Return whether a URL belongs to this static site."""
    return (not parsed.scheme and not parsed.netloc) or parsed.hostname in PUBLIC_HOSTS


def is_asset_url(link: Link, path: str) -> bool:
    """Distinguish a missing file from a missing generated page."""
    if link.attribute == "src" or path.startswith("/static/"):
        return True
    return bool(Path(path).suffix)


def resolve_internal_url(url: str, source_url: str) -> str:
    """Resolve a relative or same-site URL to an absolute path in the build."""
    resolved = urljoin(f"https://palewi.re{source_url}", url)
    return unquote(urlsplit(resolved).path)


def validate_external_url(url: str) -> str | None:
    """Return an error for a malformed external HTTP(S) URL, if any."""
    if any(character.isspace() for character in url):
        return "contains whitespace"
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError:
        return "has an invalid host or port"
    if parsed.scheme in {"http", "https"} and not hostname:
        return "is missing a host"
    return None


def parse_xml_urls(path: Path, element_path: str) -> set[str]:
    """Read URL text values from a generated XML document."""
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError) as error:
        raise ValueError(f"{path.name} could not be parsed: {error}") from error
    return {
        element.text.strip()
        for element in root.findall(element_path)
        if element.text is not None and element.text.strip()
    }


def post_urls(build_dir: Path) -> list[str]:
    """Return generated post URLs in reverse publication-date order."""
    posts = [
        public_url_for_page(path, build_dir)
        for path in build_dir.glob("posts/*/*/*/*/index.html")
        if POST_PATH_PATTERN.match(public_url_for_page(path, build_dir))
    ]
    return sorted(posts, reverse=True)


def check_post_coverage(build_dir: Path, posts: list[str]) -> list[Finding]:
    """Confirm every generated post is in its sitemap and recent feed window."""
    findings: list[Finding] = []
    sitemap_path = build_dir / "sitemap-posts.xml"
    feed_path = build_dir / "feeds" / "posts" / "index.xml"
    try:
        sitemap_urls = parse_xml_urls(sitemap_path, ".//{*}loc")
    except ValueError as error:
        findings.append(Finding("invalid-sitemap", "sitemap-posts.xml", str(error)))
        sitemap_urls = set()
    try:
        feed_urls = parse_xml_urls(feed_path, ".//item/link")
    except ValueError as error:
        findings.append(Finding("invalid-feed", "feeds/posts/index.xml", str(error)))
        feed_urls = set()

    for post in posts:
        absolute_url = f"https://palewi.re{post}"
        if absolute_url not in sitemap_urls:
            findings.append(
                Finding("missing-sitemap-post", "sitemap-posts.xml", f"does not include generated post {post}")
            )

    for post in posts[:FEED_POST_LIMIT]:
        absolute_url = f"https://palewi.re{post}"
        if absolute_url not in feed_urls:
            findings.append(
                Finding("missing-feed-post", "feeds/posts/index.xml", f"does not include recent generated post {post}")
            )
    return findings


def check_built_site(build_dir: Path) -> list[Finding]:
    """Check a baked site without opening a network connection."""
    urls = build_urls(build_dir)
    findings: list[Finding] = []
    canonical_sources: dict[str, list[str]] = defaultdict(list)

    for page_path in sorted(build_dir.rglob("*.html")):
        relative_path = page_path.relative_to(build_dir).as_posix()
        parser = PageParser()
        parser.feed(page_path.read_text(encoding="utf-8"))
        parser.close()
        source_url = public_url_for_page(page_path, build_dir)

        if relative_path not in ERROR_PAGES:
            for canonical in parser.canonicals:
                canonical_sources[canonical].append(relative_path)

        for message in parser.image_issues:
            findings.append(Finding("image-alt", relative_path, message))

        for link in parser.links:
            url = link.value.strip()
            if not url or url.startswith("#"):
                continue
            if link.attribute == "href" and HOSTNAME_WITHOUT_SCHEME.match(url):
                findings.append(
                    Finding(
                        "invalid-external-url",
                        relative_path,
                        f'{link.tag}[{link.attribute}="{link.value}"] is missing an HTTP(S) scheme',
                    )
                )
                continue
            try:
                parsed = urlsplit(url)
            except ValueError:
                findings.append(
                    Finding(
                        "invalid-external-url",
                        relative_path,
                        f'{link.tag}[{link.attribute}="{link.value}"] has an invalid host or port',
                    )
                )
                continue
            if not is_internal_url(parsed):
                error = validate_external_url(url)
                if error:
                    findings.append(
                        Finding(
                            "invalid-external-url",
                            relative_path,
                            f'{link.tag}[{link.attribute}="{link.value}"] {error}',
                        )
                    )
                continue
            if parsed.scheme not in {"", "http", "https"}:
                continue

            target_path = resolve_internal_url(url, source_url)
            if target_path in urls:
                continue
            code = "missing-local-asset" if is_asset_url(link, target_path) else "missing-generated-page"
            kind = "local asset" if code == "missing-local-asset" else "generated page"
            findings.append(
                Finding(
                    code,
                    relative_path,
                    f'{link.tag}[{link.attribute}="{link.value}"] targets absent {kind} {target_path}',
                )
            )

    for canonical, sources in sorted(canonical_sources.items()):
        if len(sources) > 1:
            findings.append(
                Finding(
                    "duplicate-canonical",
                    ", ".join(sources),
                    f"canonical URL {canonical} is used by {len(sources)} generated pages",
                )
            )

    findings.extend(check_post_coverage(build_dir, post_urls(build_dir)))
    return sorted(findings, key=lambda finding: (finding.code, finding.source, finding.message))


def load_baseline(path: Path) -> set[str]:
    """Load exact finding fingerprints acknowledged as existing quality debt."""
    if not path.exists():
        return set()
    return {
        line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#")
    }


@click.command()
@click.option(
    "--build-dir",
    type=click.Path(path_type=Path, exists=True, file_okay=False),
    default=Path("dist"),
    show_default=True,
    help="Directory generated by django-bakery.",
)
@click.option(
    "--baseline",
    type=click.Path(path_type=Path, dir_okay=False),
    default=DEFAULT_BASELINE_PATH,
    show_default=True,
    help="Exact known findings that should be reported without failing the gate.",
)
@click.option("--report-known", is_flag=True, help="Print acknowledged findings as well as new failures.")
def cli(build_dir: Path, baseline: Path, report_known: bool) -> None:
    """Validate generated static-site content without network access."""
    findings = check_built_site(build_dir)
    known_fingerprints = load_baseline(baseline)
    known = [finding for finding in findings if finding.fingerprint() in known_fingerprints]
    new = [finding for finding in findings if finding.fingerprint() not in known_fingerprints]
    if report_known:
        click.echo("\n".join(finding.format() for finding in findings))
    if new:
        details = "\n".join(finding.format() for finding in new)
        raise click.ClickException(f"{len(new)} new built-site quality issue(s):\n{details}")
    suffix = f" ({len(known)} documented existing issue(s))" if known else ""
    click.echo(f"Built-site quality check passed for {build_dir}{suffix}.")


if __name__ == "__main__":
    cli()
