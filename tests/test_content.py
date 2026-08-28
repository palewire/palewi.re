"""Tests for YAML content loading."""

import datetime
from pathlib import Path

import pytest
import yaml

from coltrane.content_loaders import (
    ContentError,
    Doc,
    group_apps,
    group_code,
    load_apps,
    load_awards,
    load_bots,
    load_clip_updates,
    load_clips,
    load_code,
    load_docs,
    load_posts,
    load_slogans,
    load_talks,
    random_slogan,
)


def test_bio_meta_yaml_loads():
    """bio_meta.yaml must have an emails key with at least one entry."""
    path = Path(__file__).resolve().parent.parent / "coltrane" / "content" / "bio_meta.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "emails" in data
    assert len(data["emails"]) >= 1


def test_bio_skills_yaml_loads():
    """bio_skills.yaml must have a skills key with at least one entry."""
    path = Path(__file__).resolve().parent.parent / "coltrane" / "content" / "bio_skills.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "skills" in data
    assert len(data["skills"]) >= 1


def test_bio_md_exists_and_non_empty():
    """bio.md must exist and contain content."""
    path = Path(__file__).resolve().parent.parent / "coltrane" / "content" / "bio.md"
    content = path.read_text(encoding="utf-8")
    assert len(content) > 100


# ---------------------------------------------------------------------------
# awards.yaml
# ---------------------------------------------------------------------------


def test_awards_yaml_loads():
    """Production awards.yaml loads without error."""
    awards = load_awards()
    assert len(awards) > 0


def test_awards_sorted_descending_year():
    """Awards are sorted by descending year."""
    awards = load_awards()
    years_with_year = [a.year for a in awards if a.year is not None]
    assert years_with_year == sorted(years_with_year, reverse=True)


def test_award_missing_title_raises(tmp_path):
    p = tmp_path / "awards.yaml"
    p.write_text("awards:\n  - url: http://example.com\n")
    with pytest.raises(ContentError, match="title"):
        load_awards(p)


def test_award_bad_year_type_raises(tmp_path):
    p = tmp_path / "awards.yaml"
    p.write_text("awards:\n  - title: A\n    year: '2024'\n")
    with pytest.raises(ContentError, match="year"):
        load_awards(p)


def test_awards_empty_list_ok(tmp_path):
    p = tmp_path / "awards.yaml"
    p.write_text("awards: []\n")
    assert load_awards(p) == []


# ---------------------------------------------------------------------------
# apps.yaml
# ---------------------------------------------------------------------------


def test_apps_yaml_loads():
    apps = load_apps()
    assert len(apps) == 14
    assert all(app.description for app in apps)
    descriptions = {app.title: app.description for app in apps}
    assert descriptions["the e.e. cummings free poetry archive"].startswith(
        "A collection of the work of Edward Estlin Cummings"
    )
    assert descriptions["fivethirtyeightindex"].startswith("Explore 38,593")
    assert [category.title for category in group_apps(apps)] == [
        "Archiving",
        "Databases",
        "Social media bots",
        "Personal websites",
    ]


def test_app_requires_http_url(tmp_path):
    path = tmp_path / "apps.yaml"
    path.write_text("apps:\n  - title: Example\n    type: personal\n    url: not-a-url\n")

    with pytest.raises(ContentError, match="HTTP\\(S\\) URL"):
        load_apps(path)


def test_app_duplicate_url_raises(tmp_path):
    path = tmp_path / "apps.yaml"
    path.write_text(
        "apps:\n"
        "  - title: One\n    type: personal\n    url: https://example.com/\n"
        "  - title: Two\n    type: personal\n    url: https://example.com/\n"
    )

    with pytest.raises(ContentError, match="duplicate"):
        load_apps(path)


def test_apps_empty_list_ok(tmp_path):
    path = tmp_path / "apps.yaml"
    path.write_text("apps: []\n")
    assert load_apps(path) == []


# ---------------------------------------------------------------------------
# code.yaml
# ---------------------------------------------------------------------------


def test_code_yaml_loads_as_one_alphabetical_catalog():
    projects = load_code()
    assert len(projects) == 250
    assert [project.title.casefold() for project in projects] == sorted(
        project.title.casefold() for project in projects
    )
    assert [category.title for category in group_code(projects)] == [
        "Python",
        "JavaScript",
        "Data",
        "Other",
        "Inactive",
    ]


def test_code_rejects_duplicate_titles(tmp_path):
    path = tmp_path / "code.yaml"
    path.write_text(
        "code:\n"
        "  - title: Example\n    type: python\n    url: https://github.com/example/one\n"
        "  - title: example\n    type: python\n    url: https://github.com/example/two\n"
    )

    with pytest.raises(ContentError, match="duplicate code project title"):
        load_code(path)


# ---------------------------------------------------------------------------
# clips.yaml
# ---------------------------------------------------------------------------


def test_clips_yaml_loads():
    clips = load_clips()
    assert len(clips) > 0


def test_clips_sorted_descending_date():
    clips = load_clips()
    dates = [c.date for c in clips]
    assert dates == sorted(dates, reverse=True)


def test_clip_invalid_type_raises(tmp_path):
    p = tmp_path / "clips.yaml"
    p.write_text("clips:\n  - title: T\n    type: invalid\n    date: '2024-01-01'\n    url: http://x.com\n")
    with pytest.raises(ContentError, match="type"):
        load_clips(p)


def test_clip_updates_remove_catalog_duplicates(tmp_path, monkeypatch):
    path = tmp_path / "clips.yaml"
    path.write_text(
        "clips:\n"
        "  - title: Same title\n    type: software\n    date: '2024-01-03'\n    url: https://updates.example.com/\n"
        "  - title: Same URL\n    type: software\n    date: '2024-01-02'\n    url: https://code.example.com/\n"
        "  - title: Release name\n    catalog_title: Same title\n    type: software\n"
        "    date: '2024-01-01'\n    url: https://updates.example.com/alias/\n"
        "  - title: New release\n    type: software\n    date: '2023-01-01'\n    url: https://updates.example.com/new/\n"
    )
    monkeypatch.setattr("coltrane.content_loaders.CONTENT_PATH", tmp_path)
    catalog = [
        Doc(
            title="Same title",
            type="software",
            url="https://docs.example.com/",
            repository_url="https://code.example.com/",
        )
    ]

    assert [clip.title for clip in load_clip_updates("software", catalog)] == ["New release"]


def test_clip_duplicate_url_raises(tmp_path):
    p = tmp_path / "clips.yaml"
    p.write_text(
        "clips:\n"
        "  - title: A\n    type: story\n    date: '2024-01-01'\n    url: http://x.com\n"
        "  - title: B\n    type: story\n    date: '2024-01-02'\n    url: http://x.com\n"
    )
    with pytest.raises(ContentError, match="duplicate"):
        load_clips(p)


def test_clip_bad_date_raises(tmp_path):
    p = tmp_path / "clips.yaml"
    p.write_text("clips:\n  - title: T\n    type: story\n    date: 'not-a-date'\n    url: http://x.com\n")
    with pytest.raises(ContentError, match="date"):
        load_clips(p)


def test_clip_accepts_yaml_date_values(tmp_path):
    p = tmp_path / "clips.yaml"
    p.write_text("clips:\n  - title: T\n    type: story\n    date: 2024-01-01\n    url: http://x.com\n")

    assert load_clips(p)[0].date == datetime.date(2024, 1, 1)


def test_clip_only_links_http_urls(tmp_path):
    path = tmp_path / "clips.yaml"
    path.write_text(
        "clips:\n"
        "  - title: Linked\n    type: story\n    date: '2024-01-01'\n    url: https://example.com/\n"
        "  - title: Lost\n    type: story\n    date: '2023-01-01'\n    url: Original URL lost\n"
    )

    linked, lost = load_clips(path)
    assert linked.is_linkable
    assert not lost.is_linkable


def test_clip_can_link_to_preserved_copy(tmp_path):
    path = tmp_path / "clips.yaml"
    path.write_text(
        "clips:\n"
        "  - title: Preserved\n"
        "    type: story\n"
        "    date: '2024-01-01'\n"
        "    url: https://example.com/gone\n"
        "    link_url: https://web.archive.org/web/20240101/https://example.com/gone\n"
    )

    clip = load_clips(path)[0]
    assert clip.display_url.startswith("https://web.archive.org/")
    assert clip.is_linkable


def test_clip_link_url_error_names_the_field(tmp_path):
    path = tmp_path / "clips.yaml"
    path.write_text(
        "clips:\n"
        "  - title: Broken fallback\n"
        "    type: story\n"
        "    date: '2024-01-01'\n"
        "    url: https://example.com/gone\n"
        "    link_url: not-a-url\n"
    )

    with pytest.raises(ContentError, match="field 'link_url' must be an HTTP\\(S\\) URL"):
        load_clips(path)


def test_clip_accepts_wayback_metadata(tmp_path):
    p = tmp_path / "clips.yaml"
    p.write_text(
        "clips:\n"
        "  - title: T\n"
        "    type: story\n"
        "    date: '2024-01-01'\n"
        "    url: https://example.com/story\n"
        "    archive_url: https://web.archive.org/web/20240101000000/https://example.com/story\n"
    )

    clip = load_clips(p)[0]

    assert clip.archive_url.startswith("https://web.archive.org/")
    assert clip.archive_exemption == ""


def test_clip_rejects_invalid_or_conflicting_archive_metadata(tmp_path):
    p = tmp_path / "clips.yaml"
    p.write_text(
        "clips:\n"
        "  - title: T\n"
        "    type: story\n"
        "    date: '2024-01-01'\n"
        "    url: https://example.com/story\n"
        "    archive_url: https://example.com/not-wayback\n"
    )
    with pytest.raises(ContentError, match="archive_url"):
        load_clips(p)

    p.write_text(
        "clips:\n"
        "  - title: T\n"
        "    type: story\n"
        "    date: '2024-01-01'\n"
        "    url: https://example.com/story\n"
        "    archive_url: https://web.archive.org/web/20240101000000/https://example.com/story\n"
        "    archive_exemption: Publisher blocks archiving\n"
    )
    with pytest.raises(ContentError, match="cannot have both"):
        load_clips(p)


def test_clips_empty_list_ok(tmp_path):
    p = tmp_path / "clips.yaml"
    p.write_text("clips: []\n")
    assert load_clips(p) == []


# ---------------------------------------------------------------------------
# talks.yaml
# ---------------------------------------------------------------------------


def test_talks_yaml_loads():
    talks = load_talks()
    assert len(talks) > 0


def test_talks_sorted_descending_date():
    talks = load_talks()
    dates = [t.date for t in talks]
    assert dates == sorted(dates, reverse=True)


def test_talk_optional_fields_default_empty(tmp_path):
    p = tmp_path / "talks.yaml"
    p.write_text("talks:\n  - title: T\n    venue: V\n    location: L\n    date: '2024-01-01'\n")
    talks = load_talks(p)
    assert talks[0].video_url == ""
    assert talks[0].slides_url == ""


def test_talk_missing_required_field_raises(tmp_path):
    p = tmp_path / "talks.yaml"
    p.write_text("talks:\n  - title: T\n    venue: V\n    date: '2024-01-01'\n")
    with pytest.raises(ContentError, match="location"):
        load_talks(p)


# ---------------------------------------------------------------------------
# docs.yaml
# ---------------------------------------------------------------------------


def test_docs_yaml_loads():
    docs = load_docs()
    assert len(docs) > 0
    assert all(doc.repository_url for doc in docs)


def test_docs_sorted_by_type_then_title():
    docs = load_docs()
    keys = [(d.type, d.title) for d in docs]
    assert keys == sorted(keys)


def test_doc_invalid_type_raises(tmp_path):
    p = tmp_path / "docs.yaml"
    p.write_text("docs:\n  - title: D\n    type: blog\n    url: http://x.com\n")
    with pytest.raises(ContentError, match="type"):
        load_docs(p)


def test_doc_duplicate_url_raises(tmp_path):
    p = tmp_path / "docs.yaml"
    p.write_text(
        "docs:\n"
        "  - title: A\n    type: software\n    url: http://x.com\n"
        "  - title: B\n    type: software\n    url: http://x.com\n"
    )
    with pytest.raises(ContentError, match="duplicate"):
        load_docs(p)


def test_doc_description_optional(tmp_path):
    p = tmp_path / "docs.yaml"
    p.write_text("docs:\n  - title: D\n    type: software\n    url: http://x.com\n")
    docs = load_docs(p)
    assert docs[0].description == ""
    assert docs[0].repository_url == ""


def test_doc_repository_url_null_is_optional(tmp_path):
    p = tmp_path / "docs.yaml"
    p.write_text("docs:\n  - title: D\n    type: software\n    url: http://x.com\n    repository_url: null\n")

    assert load_docs(p)[0].repository_url == ""


def test_doc_repository_url_valid_and_does_not_change_order(tmp_path):
    p = tmp_path / "docs.yaml"
    p.write_text(
        "docs:\n"
        "  - title: Z\n    type: software\n    url: http://z.example.com\n"
        "    repository_url: https://code.example.com/z\n"
        "  - title: A\n    type: software\n    url: http://a.example.com\n"
        "    repository_url: http://code.example.com/a\n"
    )

    docs = load_docs(p)

    assert [doc.title for doc in docs] == ["A", "Z"]
    assert docs[0].repository_url == "http://code.example.com/a"
    assert docs[1].repository_url == "https://code.example.com/z"


@pytest.mark.parametrize(
    "repository_url",
    ["code.example.com/project", "ftp://code.example.com/project", "https://"],
)
def test_doc_invalid_repository_url_raises(tmp_path, repository_url):
    p = tmp_path / "docs.yaml"
    p.write_text(
        f"docs:\n  - title: D\n    type: software\n    url: http://x.com\n    repository_url: {repository_url}\n"
    )

    with pytest.raises(ContentError, match="doc 'D'.*repository_url.*HTTP\\(S\\) URL"):
        load_docs(p)


def test_doc_repository_url_must_be_a_string(tmp_path):
    p = tmp_path / "docs.yaml"
    p.write_text("docs:\n  - title: D\n    type: software\n    url: http://x.com\n    repository_url: 123\n")

    with pytest.raises(ContentError, match="doc 'D'.*repository_url.*must be a string"):
        load_docs(p)


def test_doc_duplicate_repository_url_raises_with_title(tmp_path):
    p = tmp_path / "docs.yaml"
    p.write_text(
        "docs:\n"
        "  - title: A\n    type: software\n    url: http://a.example.com\n"
        "    repository_url: https://code.example.com/shared\n"
        "  - title: B\n    type: software\n    url: http://b.example.com\n"
        "    repository_url: https://code.example.com/shared\n"
    )

    with pytest.raises(ContentError, match="duplicate doc repository_url.*doc 'B'"):
        load_docs(p)


def test_docs_empty_list_ok(tmp_path):
    p = tmp_path / "docs.yaml"
    p.write_text("docs: []\n")
    assert load_docs(p) == []


# ---------------------------------------------------------------------------
# slogans.yaml
# ---------------------------------------------------------------------------


def test_slogans_yaml_loads():
    """Production slogans.yaml loads without error."""
    slogans = load_slogans()
    assert len(slogans) > 0


def test_slogans_sorted_alphabetically():
    """Slogans are sorted alphabetically by title."""
    slogans = load_slogans()
    titles = [s.title for s in slogans]
    assert titles == sorted(titles)


def test_slogan_missing_title_raises(tmp_path):
    p = tmp_path / "slogans.yaml"
    p.write_text("slogans:\n  - note: oops\n")
    with pytest.raises(ContentError, match="title"):
        load_slogans(p)


def test_slogans_empty_list_ok(tmp_path):
    p = tmp_path / "slogans.yaml"
    p.write_text("slogans: []\n")
    assert load_slogans(p) == []


def test_slogans_bad_top_level_raises(tmp_path):
    p = tmp_path / "slogans.yaml"
    p.write_text("- a\n- b\n")
    with pytest.raises(ContentError, match="mapping"):
        load_slogans(p)


def test_random_slogan_returns_slogan(tmp_path):
    p = tmp_path / "slogans.yaml"
    p.write_text("slogans:\n  - title: only one\n")
    result = random_slogan(p)
    assert result is not None
    assert result.title == "only one"


def test_random_slogan_empty_returns_none(tmp_path):
    p = tmp_path / "slogans.yaml"
    p.write_text("slogans: []\n")
    assert random_slogan(p) is None


# ---------------------------------------------------------------------------
# bots.yaml
# ---------------------------------------------------------------------------


def test_bots_yaml_loads():
    """Production bots.yaml loads without error."""
    bots = load_bots()
    assert len(bots) > 0


def test_bots_order_preserved():
    """Bots preserve the order defined in the YAML file."""
    bots = load_bots()
    # The first bot in the file is @DivineAnnDvorak
    assert bots[0].title == "@DivineAnnDvorak"


def test_bots_twitter_url_optional(tmp_path):
    """A bot with an empty twitter_url is valid."""
    p = tmp_path / "bots.yaml"
    p.write_text("bots:\n  - title: '@TestBot'\n    mastodon_url: 'https://example.com/@test'\n    twitter_url: ''\n")
    bots = load_bots(p)
    assert bots[0].twitter_url == ""


def test_bots_missing_mastodon_url_raises(tmp_path):
    p = tmp_path / "bots.yaml"
    p.write_text("bots:\n  - title: '@Test'\n    twitter_url: ''\n")
    with pytest.raises(ContentError, match="mastodon_url"):
        load_bots(p)


def test_bots_duplicate_mastodon_url_raises(tmp_path):
    p = tmp_path / "bots.yaml"
    p.write_text(
        "bots:\n"
        "  - title: '@A'\n    mastodon_url: 'https://m.example.com/@a'\n"
        "  - title: '@B'\n    mastodon_url: 'https://m.example.com/@a'\n"
    )
    with pytest.raises(ContentError, match="duplicate"):
        load_bots(p)


def test_bots_duplicate_twitter_url_raises(tmp_path):
    p = tmp_path / "bots.yaml"
    p.write_text(
        "bots:\n"
        "  - title: '@A'\n    mastodon_url: 'https://m.example.com/@a'\n    twitter_url: 'https://twitter.com/shared'\n"
        "  - title: '@B'\n    mastodon_url: 'https://m.example.com/@b'\n    twitter_url: 'https://twitter.com/shared'\n"
    )
    with pytest.raises(ContentError, match="duplicate"):
        load_bots(p)


def test_bots_invalid_mastodon_url_raises(tmp_path):
    p = tmp_path / "bots.yaml"
    p.write_text("bots:\n  - title: '@X'\n    mastodon_url: 'not-a-url'\n")
    with pytest.raises(ContentError, match="URL"):
        load_bots(p)


def test_bots_invalid_twitter_url_raises(tmp_path):
    p = tmp_path / "bots.yaml"
    p.write_text("bots:\n  - title: '@X'\n    mastodon_url: 'https://example.com/@x'\n    twitter_url: 'not-a-url'\n")
    with pytest.raises(ContentError, match="URL"):
        load_bots(p)


def test_bots_empty_list_ok(tmp_path):
    p = tmp_path / "bots.yaml"
    p.write_text("bots: []\n")
    assert load_bots(p) == []


@pytest.mark.parametrize(
    ("loader", "key"),
    [
        (load_awards, "awards"),
        (load_apps, "apps"),
        (load_code, "code"),
        (load_clips, "clips"),
        (load_talks, "talks"),
        (load_docs, "docs"),
        (load_slogans, "slogans"),
        (load_bots, "bots"),
    ],
)
def test_yaml_loaders_reject_invalid_top_level_and_records(tmp_path, loader, key):
    path = tmp_path / f"{key}.yaml"
    path.write_text("- not-a-mapping\n")
    with pytest.raises(ContentError, match="top-level structure"):
        loader(path)

    path.write_text(f"{key}: not-a-list\n")
    with pytest.raises(ContentError, match="must be a list"):
        loader(path)

    path.write_text(f"{key}:\n  - not-a-mapping\n")
    with pytest.raises(ContentError, match="must be a mapping"):
        loader(path)


def test_optional_content_fields_validate_their_types(tmp_path):
    path = tmp_path / "awards.yaml"
    path.write_text("awards:\n  - title: A\n    url: 123\n")
    with pytest.raises(ContentError, match="must be a string"):
        load_awards(path)

    path.write_text("awards:\n  - title: A\n    url: null\n")
    assert load_awards(path)[0].url == ""


def test_markdown_post_loader_validates_all_front_matter_edges(tmp_path):
    missing_directory = tmp_path / "missing"
    with pytest.raises(ContentError, match="does not exist"):
        load_posts(missing_directory)

    post = tmp_path / "post.md"
    post.write_text("<p>Missing front matter</p>", encoding="utf-8")
    with pytest.raises(ContentError, match="must begin"):
        load_posts(tmp_path)

    post.write_text("---\ntitle: Example\n", encoding="utf-8")
    with pytest.raises(ContentError, match="not closed"):
        load_posts(tmp_path)

    post.write_text("---\ninvalid: [\n---\n<p>Body</p>", encoding="utf-8")
    with pytest.raises(ContentError, match="invalid YAML"):
        load_posts(tmp_path)

    post.write_text("---\n- not-a-mapping\n---\n<p>Body</p>", encoding="utf-8")
    with pytest.raises(ContentError, match="must be a mapping"):
        load_posts(tmp_path)


@pytest.mark.parametrize(
    ("front_matter", "message"),
    [
        ("title: Example\nslug: bad slug\npublished_at: '2025-01-01T12:00:00-08:00'", "slug"),
        ("title: Example\nslug: example\npublished_at: '2025-01-01T12:00:00'", "timezone"),
        ("title: Example\nslug: example\npublished_at: not-a-datetime", "ISO 8601"),
        ("title: Example\nslug: example\npublished_at: '2025-01-01T12:00:00-08:00'\nwordpress_id: 0", "positive"),
    ],
)
def test_markdown_post_loader_rejects_invalid_fields(tmp_path, front_matter, message):
    post = tmp_path / "post.md"
    post.write_text(f"---\n{front_matter}\n---\n<p>Body</p>", encoding="utf-8")

    with pytest.raises(ContentError, match=message):
        load_posts(tmp_path)


def test_markdown_post_loader_accepts_yaml_dates_and_optional_values(tmp_path):
    post = tmp_path / "post.md"
    post.write_text(
        "---\n"
        "title: Example\n"
        "slug: example\n"
        "published_at: '2025-01-01T12:00:00-08:00'\n"
        "repr_image: null\n"
        "---\n"
        "<p>Body</p>",
        encoding="utf-8",
    )

    loaded_post = load_posts(tmp_path)[0]
    assert loaded_post.published_at == datetime.datetime(
        2025, 1, 1, 12, tzinfo=datetime.timezone(datetime.timedelta(hours=-8))
    )
    assert loaded_post.repr_image == ""
