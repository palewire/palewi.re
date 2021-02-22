"""
Snippet adapted from http://www.djangosnippets.org/snippets/360/
"""
from pygments.lexers import LEXERS, get_lexer_by_name
from pygments import highlight
from pygments.formatters import HtmlFormatter
from BeautifulSoup import BeautifulSoup

# a tuple of known lexer names
_lexer_names = reduce(lambda a, b: a + b[2], LEXERS.itervalues(), ())


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
    soup = BeautifulSoup(raw_html)
    for tag in soup.findAll("pre"):
        lexer_name = tag.get("lang").lower()
        linenos = tag.get("linenos", False) or False
        _formatter = HtmlFormatter(cssclass="source", linenos=linenos)
        if lexer_name and lexer_name in _lexer_names:
            lexer = get_lexer_by_name(lexer_name, stripnl=True, encoding="UTF-8")
            tag.replaceWith(highlight(tag.renderContents(), lexer, _formatter))

    return unicode(soup)
