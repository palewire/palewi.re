"""Create a valid, file-backed public blog post."""

from __future__ import annotations

import fcntl
import os
import re
import tempfile
import unicodedata
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import click
import yaml

from coltrane.content_loaders import ContentError, load_posts, parse_los_angeles_datetime

DEFAULT_POSTS_PATH = Path(__file__).resolve().parents[1] / "coltrane" / "content" / "posts"
BODY_PLACEHOLDER = """<!-- Replace this placeholder with the published post body in raw HTML. -->
<p>Write your post body as raw HTML.</p>
"""


class PostAuthoringError(ValueError):
    """Raised when a new post would be invalid or conflict with published content."""


def slugify(title: str) -> str:
    """Return an ASCII URL-safe slug generated from a post title."""
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode().lower()
    return "-".join(re.findall(r"[a-z0-9]+", ascii_title))


def post_url(published_at: datetime, slug: str) -> str:
    """Return the public URL for a date and slug."""
    return f"/posts/{published_at:%Y}/{published_at:%m}/{published_at:%d}/{slug}/"


def post_content(title: str, slug: str, published_at: str) -> str:
    """Render front matter and the raw-HTML body placeholder."""
    front_matter = yaml.safe_dump(
        {"title": title, "slug": slug, "published_at": published_at},
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    return f"---\n{front_matter}---\n{BODY_PLACEHOLDER}"


def write_new_file(destination: Path, content: str) -> None:
    """Atomically create a file without replacing a concurrent destination."""
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(content)
            temporary_path = Path(temporary_file.name)
        os.link(temporary_path, destination)
    except FileExistsError as error:
        raise PostAuthoringError(f"{destination}: destination already exists") from error
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


@contextmanager
def lock_posts_directory(posts_path: Path) -> Iterator[None]:
    """Hold an interprocess lock on the posts directory."""
    descriptor = os.open(posts_path, os.O_RDONLY)
    locked = False
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        locked = True
        yield
    finally:
        if locked:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def create_post(title: str, published_at_value: str, posts_path: Path = DEFAULT_POSTS_PATH) -> Path:
    """Validate and create a new public Markdown post."""
    title = title.strip()
    if not title:
        raise PostAuthoringError("title must not be empty")

    slug = slugify(title)
    if not slug:
        raise PostAuthoringError("title must contain letters or numbers that can form a URL-safe slug")

    published_at = parse_los_angeles_datetime(published_at_value, "published_at", "post authoring")
    url = post_url(published_at, slug)
    content = post_content(title, slug, published_at.isoformat())
    with lock_posts_directory(posts_path):
        destination = posts_path / f"{published_at:%Y-%m-%d}--{slug}.md"
        if destination.exists():
            raise PostAuthoringError(f"{destination}: destination already exists")

        posts = load_posts(posts_path)
        if any(post.get_absolute_url() == url for post in posts):
            raise PostAuthoringError(f"duplicate public URL '{url}'")
        if any(post.slug == slug for post in posts):
            raise PostAuthoringError(f"duplicate post slug '{slug}'")

        write_new_file(destination, content)
    return destination


@click.command()
@click.option("--title", required=True, prompt="Title", help="Published post title.")
@click.option(
    "--published-at",
    required=True,
    prompt="Published at",
    help="Los Angeles publication time as ISO 8601 with its correct UTC offset.",
)
@click.option(
    "--posts-path",
    type=click.Path(path_type=Path, exists=True, file_okay=False),
    default=DEFAULT_POSTS_PATH,
    show_default=True,
    help="Directory containing public Markdown posts.",
)
def cli(title: str, published_at: str, posts_path: Path) -> None:
    """Create a new public post with raw-HTML body scaffolding."""
    try:
        destination = create_post(title, published_at, posts_path)
    except (ContentError, PostAuthoringError) as error:
        raise click.ClickException(str(error)) from error

    click.echo(f"Created {destination}")
    click.echo("Next: replace the raw-HTML placeholder, run make check, then make serve or make bake to preview.")


if __name__ == "__main__":
    cli()
