"""Commands for resumable public-page archive maintenance."""

from __future__ import annotations

import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import click
import requests

from scripts.site_archive.discovery import PageDiscovery, build_seeds
from scripts.site_archive.manifest import ArchiveError, Manifest, ManifestStore, PageRecord, utc_now
from scripts.site_archive.wayback import WaybackClient

DEFAULT_MANIFEST = Path(".site-archive/manifest.json")


def report_text(manifest: Manifest) -> str:
    """Summarize known coverage without hiding unfinished discovery or errors.

    Args:
        manifest: Archive and discovery state to summarize.

    Returns:
        A Markdown report suitable for a terminal or Actions summary.

    Examples:
        ``print(report_text(Manifest()))`` displays an empty inventory.
    """
    pages = list(manifest.pages.values())
    active = [page for page in pages if page.live_status != "redirect"]
    counts = Counter(page.archive_status for page in active)
    live_counts = Counter(page.live_status for page in pages)
    errors = [page for page in active if page.last_check_status == "error"]
    lines = [
        "# Site archive coverage",
        "",
        "| Result | Pages |",
        "| --- | ---: |",
        f"| Known page URLs (excluding redirects) | {len(active)} |",
        f"| Confirmed archives | {counts['archived']} |",
        f"| Missing archives | {counts['missing']} |",
        f"| Pending capture confirmations | {counts['pending']} |",
        f"| Blocked captures | {counts['blocked']} |",
        f"| Not yet checked | {counts['unknown']} |",
        f"| Archive checks with errors | {len(errors)} |",
        f"| Live HTML pages | {live_counts['live']} |",
        f"| Live pages missing or unavailable | {live_counts['missing'] + live_counts['error']} |",
        f"| Live pages not yet checked | {live_counts['unknown']} |",
        f"| Redirect aliases (not separate pages) | {live_counts['redirect']} |",
        f"| Discovery requests remaining | {len(manifest.discovery_queue)} |",
        f"| Discovery problems | {len(manifest.discovery_errors)} |",
        "",
        f"Discovery sweep: {'finished without errors' if manifest.discovery_complete else 'unfinished or has gaps'}.",
        "Confirmed archive counts retain earlier evidence when a newer check fails; inspect the errors below.",
        "This inventory cannot prove coverage of unlinked pages published by other repositories.",
        "A page snapshot does not guarantee preservation of scripts, images, embedded media, or downloads.",
    ]
    problems = [
        *(f"{url}: {error}" for url, error in sorted(manifest.discovery_errors.items())),
        *(f"{page.url}: {page.live_error}" for page in active if page.live_error),
        *(
            f"{page.url}: {page.last_error}"
            for page in active
            if page.last_error and (page.last_check_status == "error" or page.archive_status == "blocked")
        ),
    ]
    problems = list(dict.fromkeys(problems))
    if problems:
        lines.extend(["", "## Problems", ""])
        # Escape HTML so externally supplied error text cannot become summary markup.
        for problem in problems[:50]:
            lines.append(f"- {problem.replace('<', '&lt;').replace('>', '&gt;').replace(chr(10), ' ')}")
        if len(problems) > 50:
            lines.append(f"- {len(problems) - 50} more problems are recorded in the manifest.")
    return "\n".join(lines) + "\n"


def is_due(page: PageRecord) -> bool:
    """Check whether a page is ready for another archive request.

    Args:
        page: Validated manifest record.

    Returns:
        True when no retry delay is active.

    Examples:
        ``is_due(PageRecord(url="https://palewi.re/posts/"))`` is True.
    """
    return not page.next_retry_at or datetime.fromisoformat(page.next_retry_at) <= datetime.now(UTC)


class ArchiveRun:
    """Coordinate discovery and archive requests with checkpointed progress."""

    def __init__(self, path: Path):
        """Load the manifest for a maintenance run.

        Args:
            path: Local manifest path.

        Returns:
            None.

        Examples:
            ``ArchiveRun(Path(".site-archive/manifest.json"))`` loads local state.
        """
        self.store = ManifestStore(path)
        self.manifest = self.store.load()
        self.failures: list[str] = []
        self.wayback_failed = False

    def verify(self, limit: int, deadline: float) -> None:
        """Check live pages, prioritizing pending confirmations, then fair ordering.

        Args:
            limit: Maximum page lookups.
            deadline: Monotonic time at which to stop starting work.

        Returns:
            None. Updates and saves each attempted record.

        Examples:
            ``run.verify(10, time.monotonic() + 60)`` limits lookup work.
        """
        client = WaybackClient()
        pages = sorted(
            (
                page
                for page in self.manifest.pages.values()
                if page.live_status == "live" and page.archive_status != "blocked" and is_due(page)
            ),
            key=lambda page: (
                page.archive_status != "pending",
                bool(page.last_check_at),
                page.last_check_at,
                page.url,
            ),
        )
        for page in pages[:limit]:
            if time.monotonic() >= deadline:
                break
            try:
                client.verify(page)
            except ArchiveError as error:
                self.failures.append(f"{page.url}: {error}")
            finally:
                self.store.save(self.manifest)
            # Stop this service batch rather than hammering an unavailable API.
            if page.last_check_status == "error":
                self.wayback_failed = True
                break

    def capture(self, limit: int, deadline: float) -> None:
        """Request a limited number of missing page captures.

        Args:
            limit: Maximum capture candidates.
            deadline: Monotonic time at which to stop starting work.

        Returns:
            None. Saves results, including failures, after each candidate.

        Examples:
            ``run.capture(1, time.monotonic() + 60)`` tries one missing page.
        """
        if self.wayback_failed:
            click.echo("Skipping captures because Wayback lookups failed.")
            return
        client = WaybackClient(checkpoint=lambda: self.store.save(self.manifest))
        pages = sorted(
            (
                page
                for page in self.manifest.pages.values()
                if page.live_status == "live" and page.archive_status == "missing" and is_due(page)
            ),
            key=lambda page: (page.last_submit_at, page.url),
        )
        for page in pages[:limit]:
            if time.monotonic() >= deadline:
                break
            if not self.check_live(page):
                break
            failures_before = len(self.failures)
            try:
                client.capture(page)
            except ArchiveError as error:
                self.failures.append(f"{page.url}: {error}")
            finally:
                self.store.save(self.manifest)
            if page.last_check_status == "error" or len(self.failures) > failures_before:
                break

    def check_live(self, page: PageRecord) -> bool:
        """Confirm a queued page is still public HTML before submitting it.

        Args:
            page: Capture candidate whose earlier live check may be old.

        Returns:
            Whether the page currently serves successful HTML.

        Examples:
            A page removed since the previous run is not submitted to Wayback.
        """
        discovery = PageDiscovery(self.manifest, self.store)
        try:
            discovery.visit(page.url)
        except (ArchiveError, requests.RequestException) as error:
            page.live_status = "error"
            page.live_checked_at = utc_now()
            page.live_error = str(error)
            self.manifest.discovery_errors[page.url] = str(error)
            self.manifest.discovery_complete = False
        finally:
            discovery.session.close()
            self.store.save(self.manifest)
        if page.live_status != "live":
            self.failures.append(f"{page.url}: capture deferred; live page is {page.live_status}")
            return False
        return True

    def finish(self, summary: Path | None) -> None:
        """Save progress and display a report before surfacing run failures.

        Args:
            summary: Optional Markdown report output path.

        Returns:
            None.

        Raises:
            ArchiveError: One or more requests failed during this run.

        Examples:
            ``run.finish(None)`` prints the report without writing a report file.
        """
        self.store.save(self.manifest)
        text = report_text(self.manifest)
        click.echo(text)
        if summary:
            summary.parent.mkdir(parents=True, exist_ok=True)
            summary.write_text(text, encoding="utf-8")
        if self.failures:
            raise ArchiveError("\n".join(self.failures))


@click.group()
def cli() -> None:
    """Discover, verify, capture, and report public-page archives.

    \f
    Args:
        None.

    Returns:
        None.

    Examples:
        Run ``uv run python -m scripts.site_archive report``.
    """


@cli.command()
@click.option("--manifest", type=click.Path(path_type=Path), default=DEFAULT_MANIFEST, show_default=True)
def report(manifest: Path) -> None:
    """Display saved archive state without making network requests.

    \f
    Args:
        manifest: Local archive manifest.

    Returns:
        None.

    Examples:
        Run ``uv run python -m scripts.site_archive report``.
    """
    try:
        click.echo(report_text(ManifestStore(manifest).load()))
    except (ArchiveError, OSError) as error:
        raise click.ClickException(str(error)) from error


@cli.command()
@click.option("--manifest", type=click.Path(path_type=Path), default=DEFAULT_MANIFEST, show_default=True)
@click.option("--build-dir", type=click.Path(path_type=Path), default=Path("dist"), show_default=True)
@click.option("--max-pages", type=click.IntRange(min=1), default=100, show_default=True)
@click.option("--max-seconds", type=click.IntRange(min=1), default=900, show_default=True)
@click.option("--summary", type=click.Path(path_type=Path))
def discover(manifest: Path, build_dir: Path, max_pages: int, max_seconds: int, summary: Path | None) -> None:
    """Find live pages without contacting the Internet Archive.

    \f
    Args:
        manifest: Local state path.
        build_dir: Existing static build.
        max_pages: Maximum discovery requests.
        max_seconds: Time budget in seconds.
        summary: Optional report path.

    Returns:
        None.

    Examples:
        Run ``uv run python -m scripts.site_archive discover --max-pages 10``.
    """
    execute("discover", manifest, build_dir, max_pages, 0, 0, max_seconds, True, summary)


@cli.command()
@click.option("--manifest", type=click.Path(path_type=Path), default=DEFAULT_MANIFEST, show_default=True)
@click.option("--max-checks", type=click.IntRange(min=1), default=100, show_default=True)
@click.option("--max-seconds", type=click.IntRange(min=1), default=900, show_default=True)
@click.option("--summary", type=click.Path(path_type=Path))
def verify(manifest: Path, max_checks: int, max_seconds: int, summary: Path | None) -> None:
    """Look up existing snapshots without requesting captures.

    \f
    Args:
        manifest: Local state path.
        max_checks: Maximum lookup candidates.
        max_seconds: Time budget in seconds.
        summary: Optional report path.

    Returns:
        None.

    Examples:
        Run ``uv run python -m scripts.site_archive verify --max-checks 10``.
    """
    execute("verify", manifest, Path("dist"), 0, max_checks, 0, max_seconds, True, summary)


@cli.command()
@click.option("--manifest", type=click.Path(path_type=Path), default=DEFAULT_MANIFEST, show_default=True)
@click.option("--max-captures", type=click.IntRange(min=1), default=10, show_default=True)
@click.option("--max-seconds", type=click.IntRange(min=1), default=900, show_default=True)
@click.option("--summary", type=click.Path(path_type=Path))
def capture(manifest: Path, max_captures: int, max_seconds: int, summary: Path | None) -> None:
    """Request authenticated captures for pages confirmed missing.

    \f
    Args:
        manifest: Local state path.
        max_captures: Maximum capture candidates.
        max_seconds: Time budget in seconds.
        summary: Optional report path.

    Returns:
        None.

    Examples:
        Run ``uv run python -m scripts.site_archive capture --max-captures 1``.
    """
    execute("capture", manifest, Path("dist"), 0, 0, max_captures, max_seconds, False, summary)


@cli.command()
@click.option("--manifest", type=click.Path(path_type=Path), default=DEFAULT_MANIFEST, show_default=True)
@click.option("--build-dir", type=click.Path(path_type=Path), default=Path("dist"), show_default=True)
@click.option("--max-pages", type=click.IntRange(min=1), default=100, show_default=True)
@click.option("--max-checks", type=click.IntRange(min=1), default=100, show_default=True)
@click.option("--max-captures", type=click.IntRange(min=1), default=10, show_default=True)
@click.option("--max-seconds", type=click.IntRange(min=1), default=900, show_default=True)
@click.option("--lookup-only", is_flag=True, help="Never submit new capture requests.")
@click.option("--summary", type=click.Path(path_type=Path))
def sync(
    manifest: Path,
    build_dir: Path,
    max_pages: int,
    max_checks: int,
    max_captures: int,
    max_seconds: int,
    lookup_only: bool,
    summary: Path | None,
) -> None:
    """Discover pages, check snapshots, and optionally capture missing pages.

    \f
    Args:
        manifest: Local state path.
        build_dir: Existing static build.
        max_pages: Maximum discovery requests.
        max_checks: Maximum lookup candidates.
        max_captures: Maximum capture candidates.
        max_seconds: Shared time budget in seconds.
        lookup_only: Whether to forbid capture requests.
        summary: Optional report path.

    Returns:
        None.

    Examples:
        Run ``uv run python -m scripts.site_archive sync --lookup-only``.
    """
    execute("sync", manifest, build_dir, max_pages, max_checks, max_captures, max_seconds, lookup_only, summary)


def execute(
    action: str,
    path: Path,
    build_dir: Path,
    max_pages: int,
    max_checks: int,
    max_captures: int,
    max_seconds: int,
    lookup_only: bool,
    summary: Path | None,
) -> None:
    """Run selected phases and report even when a phase fails.

    Args:
        action: Command name selecting phases.
        path: Local manifest path.
        build_dir: Existing static build.
        max_pages: Discovery request limit.
        max_checks: Archive lookup limit.
        max_captures: Capture candidate limit.
        max_seconds: Total time budget.
        lookup_only: Whether capture requests are forbidden.
        summary: Optional report destination.

    Returns:
        None.

    Raises:
        click.ClickException: Input, persistence, or network work failed.

    Examples:
        Used by the Click commands rather than called directly.
    """
    try:
        run = ArchiveRun(path)
        start = time.monotonic()
        deadline = start + max_seconds
        try:
            if action in {"discover", "sync"}:
                discovery_deadline = start + max_seconds / 3 if action == "sync" else deadline
                PageDiscovery(run.manifest, run.store).run(
                    build_seeds(build_dir), limit=max_pages, deadline=discovery_deadline
                )
                run.failures.extend(
                    f"{url}: {error}"
                    for url, error in run.manifest.discovery_errors.items()
                    if not (url.endswith("/sitemap.xml") and error in {"HTTP 403", "HTTP 404", "HTTP 410"})
                )
            if action in {"verify", "sync"}:
                verify_deadline = start + max_seconds * 2 / 3 if action == "sync" and not lookup_only else deadline
                run.verify(max_checks, verify_deadline)
            if action in {"capture", "sync"} and not lookup_only:
                run.capture(max_captures, deadline)
        except ArchiveError as error:
            run.failures.append(str(error))
        run.finish(summary)
    except (ArchiveError, OSError) as error:
        raise click.ClickException(str(error)) from error
