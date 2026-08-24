"""
Snippet adapted from http://www.djangosnippets.org/snippets/360/
"""

import functools

from bs4 import BeautifulSoup
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import LEXERS, get_lexer_by_name

# a tuple of known lexer names
_lexer_names = functools.reduce(lambda a, b: a + b[2], LEXERS.values(), ())


def pygmenter(raw_html):
    """
    Accepts raw html text for markup processing. Using BeautifulSoup
    the following constructs will be replaced
    by with pygmented highlighting. E.g.::

            <pre class="???">
                    ...
            </pre>

    Where ``???`` is the name of a supported pygments lexer, e.g.: ``python``,
    ``css``, ``html``.

    Note: Semantically, it would make more sense to wrap the code in a
    ``<code>...</code>`` tag; however, my tests using markdown.py - as well as
    markdown.pl from John Gruber - have shown that the inner HTML of the
    ``<code>`` tag is not immune to translation.
    """
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup.find_all("pre"):
        lexer_name = tag.get("lang")
        if not isinstance(lexer_name, str):
            continue
        _formatter = HtmlFormatter(cssclass="source", linenos=bool(tag.get("linenos")))
        lexer_name = lexer_name.lower()
        if lexer_name and lexer_name in _lexer_names:
            lexer = get_lexer_by_name(lexer_name, stripnl=True, encoding="UTF-8")
            tag.replace_with(highlight(tag.encode_contents(), lexer, _formatter))

    return str(soup)
