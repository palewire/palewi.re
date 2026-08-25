"""Progressively enhance SoundCloud iframes in trusted post markup."""

import re
from html import escape, unescape
from urllib.parse import urlparse

_IFRAME_RE = re.compile(
    r"(?P<iframe><iframe\b(?P<attributes>[^>]*)>(?P<content>.*?)</iframe>)",
    flags=re.IGNORECASE | re.DOTALL,
)
_SRC_RE = re.compile(r"""\bsrc\s*=\s*(?P<quote>["'])(?P<src>.*?)(?P=quote)""", flags=re.IGNORECASE | re.DOTALL)


def defer_soundcloud_embeds(markup: str) -> str:
    """Replace SoundCloud players with an accessible, on-demand player."""
    return _IFRAME_RE.sub(_defer_embed, markup)


def _defer_embed(match: re.Match[str]) -> str:
    source_match = _SRC_RE.search(match["attributes"])
    if source_match is None:
        return match["iframe"]

    source = unescape(source_match["src"])
    if urlparse(source).hostname != "w.soundcloud.com":
        return match["iframe"]

    escaped_source = escape(source, quote=True)
    iframe = match["iframe"]
    return f"""<div class="soundcloud-embed" data-soundcloud-embed>
<div class="soundcloud-embed__controls">
<p>Load the SoundCloud player for this episode.</p>
<button type="button">Load SoundCloud player</button>
<p>SoundCloud may set cookies. <a href="{escaped_source}">Open the player in SoundCloud</a>.</p>
<p class="soundcloud-embed__status" aria-live="polite"></p>
</div>
<template>{iframe}</template>
<noscript>
<p>JavaScript is disabled. The SoundCloud player is available below.</p>
{iframe}
</noscript>
</div>"""
