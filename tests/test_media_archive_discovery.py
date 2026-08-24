"""Tests for discovering playable media candidates in talks and posts."""

import datetime

from coltrane.content_loaders import MarkdownPost, Talk
from scripts.media_archive.discovery import (
    KIND_DIRECT,
    KIND_SOUNDCLOUD,
    KIND_UNKNOWN,
    KIND_VIMEO,
    KIND_YOUTUBE,
    classify_iframe_url,
    classify_media_url,
    discover_candidates,
    discover_post_occurrences,
    discover_talk_occurrence,
    normalize_url,
)


def make_post(slug: str, body_markup: str) -> MarkdownPost:
    return MarkdownPost(
        title=slug,
        slug=slug,
        published_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
        body_markup=body_markup,
    )


def make_talk(title: str, video_url: str = "") -> Talk:
    return Talk(title=title, venue="Venue", location="City", date=datetime.date(2024, 1, 1), video_url=video_url)


# ---------------------------------------------------------------------------
# normalize_url
# ---------------------------------------------------------------------------


def test_normalize_url_resolves_protocol_relative():
    assert normalize_url("//example.com/video.mp4") == "https://example.com/video.mp4"


def test_normalize_url_strips_whitespace():
    assert normalize_url("  https://example.com/video.mp4  ") == "https://example.com/video.mp4"


def test_normalize_url_resolves_site_relative_path():
    assert normalize_url("/media/mp3/clip.mp3") == "https://palewi.re/media/mp3/clip.mp3"


# ---------------------------------------------------------------------------
# classify_media_url
# ---------------------------------------------------------------------------


def test_classify_direct_media_extension():
    assert classify_media_url("https://palewire.s3.amazonaws.com/tour/9track.mp4") == KIND_DIRECT
    assert classify_media_url("//palewire.s3.amazonaws.com/tour/9track.mp4") == KIND_DIRECT


def test_classify_direct_audio_extension():
    assert classify_media_url("https://example.com/clip.mp3") == KIND_DIRECT


def test_classify_youtube_watch_url():
    assert classify_media_url("http://www.youtube.com/watch?v=iOCT8B9WyKw") == KIND_YOUTUBE
    assert classify_media_url("https://www.youtube.com/watch?v=iOCT8B9WyKw&feature=player_embedded") == KIND_YOUTUBE


def test_classify_youtube_short_url():
    assert classify_media_url("https://youtu.be/iOCT8B9WyKw") == KIND_YOUTUBE


def test_classify_vimeo_watch_url():
    assert classify_media_url("https://vimeo.com/1187819115/4fcb0378ca?share=copy") == KIND_VIMEO


def test_classify_soundcloud_track_url():
    assert classify_media_url("https://soundcloud.com/ire-nicar/a-conversation-with-ben-welsh") == KIND_SOUNDCLOUD


def test_classify_excludes_soundcloud_bare_profile():
    assert classify_media_url("https://soundcloud.com/ire-nicar") is None


def test_classify_excludes_google_slides():
    assert classify_media_url("https://docs.google.com/presentation/d/abc123/edit") is None


def test_classify_excludes_ordinary_webpage():
    assert classify_media_url("https://www.ire.org/") is None


def test_classify_excludes_image():
    assert classify_media_url("https://example.com/photo.jpg") is None


def test_classify_excludes_social_profile_link():
    assert classify_media_url("https://twitter.com/palewire") is None
    assert classify_media_url("https://www.linkedin.com/in/example") is None


def test_classify_excludes_youtube_channel_link():
    assert classify_media_url("https://www.youtube.com/@somechannel") is None


# ---------------------------------------------------------------------------
# classify_iframe_url
# ---------------------------------------------------------------------------


def test_classify_iframe_vimeo_player():
    result = classify_iframe_url("https://player.vimeo.com/video/214875675?title=0&byline=0")
    assert result == (KIND_VIMEO, "https://vimeo.com/214875675")


def test_classify_iframe_youtube_embed():
    result = classify_iframe_url("https://www.youtube.com/embed/iOCT8B9WyKw")
    assert result == (KIND_YOUTUBE, "https://www.youtube.com/watch?v=iOCT8B9WyKw")


def test_classify_iframe_soundcloud_player():
    src = (
        "https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/2099172090"
        "&color=%23ff5500&auto_play=false"
    )
    result = classify_iframe_url(src)
    assert result == (KIND_SOUNDCLOUD, "https://api.soundcloud.com/tracks/2099172090")


def test_classify_iframe_generic_returns_none():
    assert classify_iframe_url("https://docs.google.com/presentation/d/abc123/embed") is None
    assert classify_iframe_url("https://palewi.re/some/hosted/interactive/") is None


# ---------------------------------------------------------------------------
# discover_talk_occurrence
# ---------------------------------------------------------------------------


def test_discover_talk_occurrence_with_video():
    talk = make_talk("A Talk", video_url="https://vimeo.com/1187819115/4fcb0378ca?share=copy")
    result = discover_talk_occurrence(talk)
    assert result is not None
    url, kind, occurrence = result
    assert url == talk.video_url
    assert kind == KIND_VIMEO
    assert occurrence.origin_type == "talk"
    assert occurrence.location == "video_url"
    assert occurrence.raw_url == talk.video_url


def test_discover_talk_occurrence_without_video_returns_none():
    talk = make_talk("No Video")
    assert discover_talk_occurrence(talk) is None


def test_discover_talk_occurrence_unknown_host_still_included():
    talk = make_talk("Odd Host", video_url="https://example-video-host.test/watch/123")
    result = discover_talk_occurrence(talk)
    assert result is not None
    url, kind, occurrence = result
    assert kind == KIND_UNKNOWN
    assert url == talk.video_url


# ---------------------------------------------------------------------------
# discover_post_occurrences
# ---------------------------------------------------------------------------


def test_discover_post_video_tag_with_source():
    post = make_post(
        "video-post",
        '<video playsinline poster="//example.com/poster.jpg" controls>'
        '<source src="//example.com/clip.mp4" type="video/mp4"></video>',
    )
    results = discover_post_occurrences(post)
    assert len(results) == 1
    url, kind, occurrence = results[0]
    assert url == "//example.com/clip.mp4"
    assert kind == KIND_DIRECT
    assert occurrence.location == "video>source"
    assert occurrence.origin_id == "video-post"


def test_discover_post_video_src_attribute_direct():
    post = make_post("video-src", '<video src="//example.com/clip.mp4" controls></video>')
    results = discover_post_occurrences(post)
    assert len(results) == 1
    assert results[0][0] == "//example.com/clip.mp4"
    assert results[0][2].location == "video"


def test_discover_post_audio_tag_with_source():
    post = make_post(
        "audio-post", '<audio controls><source src="https://example.com/clip.mp3" type="audio/mp3"></audio>'
    )
    results = discover_post_occurrences(post)
    assert len(results) == 1
    assert results[0][1] == KIND_DIRECT
    assert results[0][2].location == "audio>source"


def test_discover_post_ignores_picture_sources():
    post = make_post(
        "picture-post",
        '<picture><source type="image/webp" srcset="/static/img/example.webp">'
        '<source type="image/png" srcset="/static/img/example.png"></picture>',
    )
    assert discover_post_occurrences(post) == []


def test_discover_post_vimeo_iframe_embed():
    post = make_post(
        "vimeo-post",
        "<div class='embed-container'><iframe src='https://player.vimeo.com/video/214875675?title=0'></iframe></div>",
    )
    results = discover_post_occurrences(post)
    assert len(results) == 1
    url, kind, occurrence = results[0]
    assert url == "https://vimeo.com/214875675"
    assert kind == KIND_VIMEO
    assert occurrence.location == "iframe"
    assert occurrence.raw_url == "https://player.vimeo.com/video/214875675?title=0"


def test_discover_post_soundcloud_iframe_and_link():
    body = (
        '<iframe src="https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/2099172090">'
        "</iframe>"
        '<a href="https://soundcloud.com/ire-nicar/a-conversation-with-ben-welsh">the podcast</a>'
    )
    post = make_post("soundcloud-post", body)
    results = discover_post_occurrences(post)
    urls = {result[0] for result in results}
    assert "https://api.soundcloud.com/tracks/2099172090" in urls
    assert "https://soundcloud.com/ire-nicar/a-conversation-with-ben-welsh" in urls


def test_discover_post_youtube_link():
    post = make_post(
        "youtube-post",
        '<a href="https://www.youtube.com/watch?v=iOCT8B9WyKw">Tweeg</a>',
    )
    results = discover_post_occurrences(post)
    assert len(results) == 1
    assert results[0][1] == KIND_YOUTUBE
    assert results[0][2].location == "a"


def test_discover_post_excludes_ordinary_links():
    post = make_post(
        "ordinary-post",
        '<a href="http://www.mattwaite.com/2008/01/02/data-ghettos/">data ghettos</a>'
        '<a href="https://twitter.com/palewire">Twitter</a>'
        '<img src="https://example.com/photo.jpg">'
        '<iframe src="https://docs.google.com/presentation/d/abc/embed"></iframe>',
    )
    assert discover_post_occurrences(post) == []


def test_discover_post_ignores_tags_missing_src_or_href():
    post = make_post(
        "no-attrs-post",
        "<video></video><iframe></iframe><a>no href here</a>",
    )
    assert discover_post_occurrences(post) == []


def test_attribute_helper_joins_multivalued_attribute():
    from bs4 import BeautifulSoup

    from scripts.media_archive.discovery import _attribute

    soup = BeautifulSoup('<video class="a b"></video>', "html.parser")
    tag = soup.find("video")
    assert _attribute(tag, "class") == "ab"
    assert _attribute(tag, "missing") is None


# ---------------------------------------------------------------------------
# discover_candidates
# ---------------------------------------------------------------------------


def test_discover_candidates_deduplicates_and_retains_occurrences():
    talk = make_talk("Talk", video_url="https://example.com/clip.mp4")
    post_one = make_post("post-one", '<video src="https://example.com/clip.mp4"></video>')
    post_two = make_post("post-two", '<video src="https://example.com/clip.mp4"></video>')

    candidates = discover_candidates([talk], [post_one, post_two])

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.url == "https://example.com/clip.mp4"
    assert len(candidate.occurrences) == 3
    origin_types = [occurrence.origin_type for occurrence in candidate.occurrences]
    assert origin_types == ["talk", "post", "post"]


def test_discover_candidates_preserves_discovery_order():
    talk = make_talk("Talk", video_url="https://example.com/first.mp4")
    post = make_post("post", '<video src="https://example.com/second.mp4"></video>')

    candidates = discover_candidates([talk], [post])

    assert [candidate.url for candidate in candidates] == [
        "https://example.com/first.mp4",
        "https://example.com/second.mp4",
    ]


def test_discover_candidates_empty_inputs():
    assert discover_candidates([], []) == []


def test_discover_candidates_resolves_site_relative_links_to_absolute_urls():
    post = make_post("relative-link-post", '<a href="/media/mp3/clip.mp3">clip</a>')

    candidates = discover_candidates([], [post])

    assert len(candidates) == 1
    assert candidates[0].url == "https://palewi.re/media/mp3/clip.mp3"
    assert candidates[0].kind == KIND_DIRECT
    assert candidates[0].occurrences[0].raw_url == "/media/mp3/clip.mp3"
