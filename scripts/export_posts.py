r"""Export database posts to a private archive and public Markdown files.

This script accepts a CSV created with PostgreSQL's ``\copy`` command. It
never connects to production or writes to the public database. The archive
directory must be outside this repository because it contains drafts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import tempfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml

LOS_ANGELES = ZoneInfo("America/Los_Angeles")
LIVE_STATUS = 1
EXPECTED_COUNTS = {1: 72, 2: 94, 3: 0}
LEGACY_PRE_PATTERN = re.compile(r"<pre\s+[^>]*\blang=", re.IGNORECASE)
PUBLIC_REPOSITORY_PATH = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ExportedPost:
    """One post exported from the production database."""

    id: int
    wordpress_id: int | None
    title: str
    slug: str
    body_markup: str
    body_html: str | None
    pub_date: datetime
    author_id: int
    status: int
    repr_image: str

    @property
    def published_at(self) -> datetime:
        """Return the original publication moment in Los Angeles time."""
        return self.pub_date.astimezone(LOS_ANGELES)

    @property
    def permalink(self) -> str:
        """Return the database-backed permalink that must remain stable."""
        return f"/posts/{self.published_at:%Y/%m/%d}/{self.slug}/"


def sha256_bytes(value: bytes) -> str:
    """Return a stable SHA-256 digest."""
    return hashlib.sha256(value).hexdigest()


def read_optional_int(value: str) -> int | None:
    """Read an optional integer from PostgreSQL CSV output."""
    return int(value) if value else None


def load_posts(csv_path: Path) -> list[ExportedPost]:
    """Parse a PostgreSQL CSV export and validate its expected columns."""
    required_columns = {
        "id",
        "wordpress_id",
        "title",
        "slug",
        "body_markup",
        "body_html",
        "pub_date",
        "author_id",
        "status",
        "repr_image",
    }
    with csv_path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None or set(reader.fieldnames) != required_columns:
            raise ValueError(f"{csv_path}: unexpected CSV columns {reader.fieldnames!r}")
        posts = [
            ExportedPost(
                id=int(row["id"]),
                wordpress_id=read_optional_int(row["wordpress_id"]),
                title=row["title"],
                slug=row["slug"],
                body_markup=row["body_markup"],
                body_html=row["body_html"] or None,
                pub_date=datetime.fromisoformat(row["pub_date"]),
                author_id=int(row["author_id"]),
                status=int(row["status"]),
                repr_image=row["repr_image"],
            )
            for row in reader
        ]
    if any(post.pub_date.tzinfo is None for post in posts):
        raise ValueError(f"{csv_path}: every publication datetime must include a timezone")
    return posts


def validate_posts(posts: list[ExportedPost]) -> Counter[int]:
    """Validate production counts and the unique public URL keys."""
    counts = Counter(post.status for post in posts)
    actual_counts = {status: counts[status] for status in EXPECTED_COUNTS}
    if (
        len(posts) != sum(EXPECTED_COUNTS.values())
        or actual_counts != EXPECTED_COUNTS
        or set(counts) - set(EXPECTED_COUNTS)
    ):
        raise ValueError(f"unexpected status counts: total={len(posts)}, statuses={dict(counts)}")
    live_posts = [post for post in posts if post.status == LIVE_STATUS]
    keys = [(post.published_at.date(), post.slug) for post in live_posts]
    if len(keys) != len(set(keys)):
        raise ValueError("live posts have duplicate publication-date/slug keys")
    slugs = [post.slug for post in live_posts]
    if len(slugs) != len(set(slugs)):
        raise ValueError("live posts have duplicate slugs")
    return counts


def post_record(post: ExportedPost) -> dict[str, Any]:
    """Serialize an archived post without changing its source values."""
    return {
        "id": post.id,
        "wordpress_id": post.wordpress_id,
        "title": post.title,
        "slug": post.slug,
        "body_markup": post.body_markup,
        "body_html": post.body_html,
        "pub_date": post.pub_date.isoformat(),
        "author_id": post.author_id,
        "status": post.status,
        "repr_image": post.repr_image,
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    """Write a deterministic JSON document."""
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def path_is_within(path: Path, parent: Path) -> bool:
    """Return whether a resolved path is the parent or one of its children."""
    return path == parent or parent in path.parents


def validate_export_paths(archive_path: Path, content_path: Path) -> tuple[Path, Path]:
    """Reject destinations that could place draft data in the public checkout."""
    resolved_archive_path = archive_path.resolve()
    resolved_content_path = content_path.resolve()
    if path_is_within(resolved_archive_path, PUBLIC_REPOSITORY_PATH):
        raise ValueError("archive path must be outside the public repository")
    if path_is_within(resolved_archive_path, resolved_content_path) or path_is_within(
        resolved_content_path, resolved_archive_path
    ):
        raise ValueError("archive path must not overlap the public content path")
    return resolved_archive_path, resolved_content_path


def write_archive_files(posts: list[ExportedPost], counts: Counter[int], archive_path: Path, source_csv: Path) -> None:
    """Write individual archive records and a checksum manifest to a staging path."""
    records_path = archive_path / "posts"
    if records_path.exists():
        shutil.rmtree(records_path)
    records_path.mkdir(parents=True)
    shutil.copy2(source_csv, archive_path / "posts.csv")

    checksum_lines: list[str] = []
    for post in posts:
        relative_path = Path("posts") / f"{post.id}.json"
        record_path = archive_path / relative_path
        write_json(record_path, post_record(post))
        checksum_lines.append(f"{sha256_bytes(record_path.read_bytes())}  {relative_path.as_posix()}")

    checksum_path = archive_path / "checksums.sha256"
    checksum_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "source": "palewire production PostgreSQL",
        "source_csv_sha256": sha256_bytes(source_csv.read_bytes()),
        "record_count": len(posts),
        "status_counts": {str(status): count for status, count in sorted(counts.items())},
        "legacy_pre_lang_count": sum(bool(LEGACY_PRE_PATTERN.search(post.body_markup)) for post in posts),
        "checksums_sha256": sha256_bytes(checksum_path.read_bytes()),
    }
    write_json(archive_path / "archive-manifest.json", manifest)


def validate_private_archive(archive_path: Path, expected_count: int, expected_counts: Counter[int]) -> None:
    """Confirm a private archive has complete, checksummed post records."""
    checksum_path = archive_path / "checksums.sha256"
    checksum_lines = checksum_path.read_text(encoding="utf-8").splitlines()
    checksums = {path: digest for digest, path in (line.split("  ", 1) for line in checksum_lines)}
    records = [
        json.loads(record_path.read_text(encoding="utf-8")) for record_path in (archive_path / "posts").glob("*.json")
    ]
    if len(records) != expected_count or len(checksums) != expected_count:
        raise ValueError("private archive record count does not match the production export")
    if Counter(record["status"] for record in records) != expected_counts:
        raise ValueError("private archive status counts do not match the production export")
    for relative_path, expected_hash in checksums.items():
        actual_hash = sha256_bytes((archive_path / relative_path).read_bytes())
        if actual_hash != expected_hash:
            raise ValueError(f"private archive checksum mismatch: {relative_path}")


def replace_private_archive(
    posts: list[ExportedPost],
    counts: Counter[int],
    archive_path: Path,
    source_csv: Path,
) -> None:
    """Stage and validate a replacement before replacing the existing archive.

    Until the new archive has been fully written and verified, the prior archive
    stays untouched. During the final swap it is retained as a sibling backup,
    so an interrupted process leaves a complete copy recoverable on disk.
    """
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path = archive_path.with_name(f".{archive_path.name}.backup")
    if backup_path.exists():
        if archive_path.exists():
            raise ValueError(f"existing backup requires manual review: {backup_path}")
        backup_path.rename(archive_path)

    staging_path = Path(tempfile.mkdtemp(prefix=f".{archive_path.name}.staging-", dir=archive_path.parent))
    if archive_path.exists():
        shutil.copytree(archive_path, staging_path, dirs_exist_ok=True)
    write_archive_files(posts, counts, staging_path, source_csv)
    validate_private_archive(staging_path, len(posts), counts)
    if archive_path.exists():
        archive_path.rename(backup_path)
    staging_path.rename(archive_path)
    if backup_path.exists():
        shutil.rmtree(backup_path)


def markdown_front_matter(post: ExportedPost) -> dict[str, str | int]:
    """Build the public metadata contract for one live post."""
    metadata: dict[str, str | int] = {
        "title": post.title,
        "slug": post.slug,
        "published_at": post.published_at.isoformat(),
    }
    if post.repr_image:
        metadata["repr_image"] = post.repr_image
    if post.wordpress_id is not None:
        metadata["wordpress_id"] = post.wordpress_id
    return metadata


def markdown_content(post: ExportedPost) -> str:
    """Return YAML front matter followed by the exact database HTML body."""
    front_matter = yaml.safe_dump(
        markdown_front_matter(post),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    return f"---\n{front_matter}---\n{post.body_markup}"


def write_public_posts(posts: list[ExportedPost], content_path: Path) -> None:
    """Write public-only Markdown posts and their non-private fingerprint."""
    posts_path = content_path / "posts"
    if posts_path.exists():
        shutil.rmtree(posts_path)
    posts_path.mkdir(parents=True)

    manifest_posts: list[dict[str, str]] = []
    for post in sorted(posts, key=lambda item: (item.published_at, item.slug)):
        filename = f"{post.published_at:%Y-%m-%d}--{post.slug}.md"
        relative_path = Path("posts") / filename
        post_path = content_path / relative_path
        post_path.write_text(markdown_content(post), encoding="utf-8")
        manifest_posts.append(
            {
                "path": relative_path.as_posix(),
                "permalink": post.permalink,
                "published_at": post.published_at.isoformat(),
                "sha256": sha256_bytes(post_path.read_bytes()),
                "body_sha256": sha256_bytes(post.body_markup.encode()),
            }
        )

    manifest_digest = sha256_bytes(
        json.dumps(manifest_posts, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    )
    manifest = {
        "schema_version": 1,
        "post_count": len(posts),
        "production_inventory": {"total": 166, "live": 72, "draft": 94, "hidden": 0},
        "legacy_pre_lang_post_count": sum(bool(LEGACY_PRE_PATTERN.search(post.body_markup)) for post in posts),
        "posts": manifest_posts,
        "posts_fingerprint_sha256": manifest_digest,
    }
    write_json(content_path / "posts-manifest.json", manifest)


def main() -> None:
    """Export validated private and public post artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--archive-path", type=Path, required=True)
    parser.add_argument("--content-path", type=Path, required=True)
    args = parser.parse_args()

    archive_path, content_path = validate_export_paths(args.archive_path, args.content_path)
    posts = load_posts(args.csv_path)
    counts = validate_posts(posts)
    replace_private_archive(posts, counts, archive_path, args.csv_path)
    write_public_posts([post for post in posts if post.status == LIVE_STATUS], content_path)


if __name__ == "__main__":
    main()
