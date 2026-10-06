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
        lexer_name = lexer_name.lower()
        if lexer_name and lexer_name in _lexer_names:
            lexer = get_lexer_by_name(lexer_name, stripnl=True, encoding="UTF-8")
            formatter = HtmlFormatter(
                cssclass="source",
                linenos=tag.has_attr("linenos"),
                style="native",
            )
            highlighted = BeautifulSoup(
                highlight(tag.get_text(), lexer, formatter),
                "html.parser",
            )
            pre = highlighted.pre
            assert pre is not None
            code = highlighted.new_tag(
                "code",
                attrs={"class": f"language-{lexer_name}"},
            )
            code.extend(pre.contents)
            pre.append(code)
            pre["aria-label"] = f"{lexer.name} code"
            assert highlighted.div is not None
            highlighted.div["data-language"] = lexer.name
            tag.replace_with(highlighted.div)

    return str(soup)
