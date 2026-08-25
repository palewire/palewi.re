from coltrane.utils.soundcloud import defer_soundcloud_embeds


def test_defers_soundcloud_iframe_with_accessible_fallback():
    markup = (
        '<iframe title="Episode" src="https://w.soundcloud.com/player/?url=episode" width="100%" height="300"></iframe>'
    )

    result = defer_soundcloud_embeds(markup)

    assert 'class="soundcloud-embed"' in result
    assert "<template><iframe" in result
    assert "<noscript>" in result
    assert "JavaScript is disabled. The SoundCloud player is available below." in result
    assert "Load SoundCloud player" in result
    assert "SoundCloud may set cookies." in result
    assert "https://w.soundcloud.com/player/?url=episode" in result


def test_normalizes_encoded_soundcloud_query_parameters():
    markup = '<iframe src="https://w.soundcloud.com/player/?url=episode&amp;color=orange"></iframe>'

    result = defer_soundcloud_embeds(markup)

    assert 'href="https://w.soundcloud.com/player/?url=episode&amp;color=orange"' in result
    assert "&amp;amp;" not in result


def test_leaves_non_soundcloud_iframe_unchanged():
    markup = '<iframe src="https://example.com/player"></iframe>'

    assert defer_soundcloud_embeds(markup) == markup
