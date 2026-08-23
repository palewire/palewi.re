"""Tests for YAML content loading."""

from pathlib import Path

import pytest
import yaml

from coltrane.content_loaders import (
    ContentError,
    load_awards,
    load_bots,
    load_clips,
    load_docs,
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


def test_bots_empty_list_ok(tmp_path):
    p = tmp_path / "bots.yaml"
    p.write_text("bots: []\n")
    assert load_bots(p) == []
