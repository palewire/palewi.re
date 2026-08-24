"""Tests for the one-time, private post-export utility."""

from collections import Counter
from datetime import UTC, datetime

import pytest

from scripts.export_posts import (
    EXPECTED_COUNTS,
    LIVE_STATUS,
    ExportedPost,
    load_posts,
    replace_private_archive,
    validate_posts,
    write_public_posts,
)


def make_post(
    post_id: int,
    *,
    status: int = LIVE_STATUS,
    slug: str | None = None,
    body_markup: str = "<p>Body</p>",
) -> ExportedPost:
    """Create a post matching the old database export shape."""
    return ExportedPost(
        id=post_id,
        wordpress_id=post_id,
        title=f"Post {post_id}",
        slug=slug or f"post-{post_id}",
        body_markup=body_markup,
        body_html=None,
        pub_date=datetime(2025, 1, 1, 12, tzinfo=UTC),
        author_id=1,
        status=status,
        repr_image="",
    )


def test_load_posts_reads_valid_csv_and_rejects_invalid_exports(tmp_path):
    csv_path = tmp_path / "posts.csv"
    csv_path.write_text(
        "id,wordpress_id,title,slug,body_markup,body_html,pub_date,author_id,status,repr_image\n"
        '1,,Example,example,"<p>Body</p>",,2025-01-01T12:00:00+00:00,1,1,\n',
        encoding="utf-8",
    )

    posts = load_posts(csv_path)

    assert posts[0].id == 1
    assert posts[0].wordpress_id is None
    assert posts[0].title == "Example"
    assert posts[0].slug == "example"

    csv_path.write_text("id,title\n1,Example\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected CSV columns"):
        load_posts(csv_path)

    csv_path.write_text(
        "id,wordpress_id,title,slug,body_markup,body_html,pub_date,author_id,status,repr_image\n"
        '1,,Example,example,"<p>Body</p>",,2025-01-01T12:00:00,1,1,\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="timezone"):
        load_posts(csv_path)


def test_validate_posts_accepts_expected_inventory_and_rejects_duplicates():
    posts = [
        *(make_post(post_id) for post_id in range(1, EXPECTED_COUNTS[LIVE_STATUS] + 1)),
        *(
            make_post(post_id, status=2)
            for post_id in range(EXPECTED_COUNTS[LIVE_STATUS] + 1, sum(EXPECTED_COUNTS.values()) + 1)
        ),
    ]

    assert validate_posts(posts) == Counter(EXPECTED_COUNTS)

    with pytest.raises(ValueError, match="unexpected status counts"):
        validate_posts(posts[:-1])

    duplicate_slug_posts = [*posts]
    duplicate_slug_posts[1] = make_post(2, slug=duplicate_slug_posts[0].slug)
    with pytest.raises(ValueError, match="duplicate publication-date/slug keys"):
        validate_posts(duplicate_slug_posts)


def test_export_writes_verified_private_and_public_artifacts(tmp_path):
    posts = [make_post(1, body_markup='<pre lang="python">print("hello")</pre>'), make_post(2, status=2)]
    counts = Counter(post.status for post in posts)
    archive_path = tmp_path / "archive"
    content_path = tmp_path / "content"
    source_csv = tmp_path / "source.csv"
    source_csv.write_text("source", encoding="utf-8")

    replace_private_archive(posts, counts, archive_path, source_csv)
    write_public_posts([post for post in posts if post.status == LIVE_STATUS], content_path)

    assert (archive_path / "posts" / "1.json").exists()
    assert (archive_path / "archive-manifest.json").exists()
    assert not (archive_path.parent / ".archive.backup").exists()
    assert (content_path / "posts" / "2025-01-01--post-1.md").exists()
    assert '"post_count": 1' in (content_path / "posts-manifest.json").read_text(encoding="utf-8")
