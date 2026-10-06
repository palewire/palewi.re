import datetime
from html.parser import HTMLParser

from bakery.feeds import BuildableFeed
from django.http import HttpRequest, JsonResponse
from django.utils.feedgenerator import Rss201rev2Feed
from django.views import View

from coltrane.content_loaders import MarkdownPost, load_posts

SITE_URL = "https://palewi.re"


class PlainTextSummaryParser(HTMLParser):
    """Extract readable text without scripts or styles from post HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.ignored_tag_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.ignored_tag_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.ignored_tag_depth:
            self.ignored_tag_depth -= 1
        elif not self.ignored_tag_depth:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self.ignored_tag_depth:
            self.parts.append(data)


def plain_text_summary(body_html: str) -> str:
    """Return a normalized plain-text summary from rendered post HTML."""
    parser = PlainTextSummaryParser()
    parser.feed(body_html)
    parser.close()
    return " ".join("".join(parser.parts).split())


def canonical_post_url(post: MarkdownPost) -> str:
    """Return a post's stable public URL."""
    return f"{SITE_URL}{post.get_absolute_url()}"


class LatestPostsRssFeed(Rss201rev2Feed):
    """Use the newest post timestamp so generated feeds are reproducible."""

    def latest_post_date(self):
        return load_posts()[0].published_at


class LatestPostsFeed(BuildableFeed):
    feed_type = LatestPostsRssFeed
    title = "palewi.re posts"
    link = "/feeds/posts/"
    description = "the latest"

    def items(self):
        return load_posts()[:10]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.body_html

    def item_pubdate(self, item: MarkdownPost) -> datetime.datetime:
        return item.published_at


class LatestPostsJsonFeed(View):
    """Serve every published post as a JSON Feed 1.1 document."""

    def get(self, _request: HttpRequest) -> JsonResponse:
        items: list[dict[str, str]] = []
        for post in load_posts():
            item = {
                "id": canonical_post_url(post),
                "url": canonical_post_url(post),
                "title": post.title,
                "date_published": post.published_at.isoformat(),
                "content_html": post.body_html,
            }
            if summary := plain_text_summary(post.body_html):
                item["summary"] = summary
            items.append(item)

        return JsonResponse(
            {
                "version": "https://jsonfeed.org/version/1.1",
                "title": "palewi.re posts",
                "home_page_url": f"{SITE_URL}/",
                "feed_url": f"{SITE_URL}/feeds/posts.json",
                "items": items,
            },
            content_type="application/feed+json; charset=utf-8",
            json_dumps_params={"ensure_ascii": False, "indent": 2},
        )
