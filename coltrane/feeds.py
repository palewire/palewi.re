from bakery.feeds import BuildableFeed
from django.utils.feedgenerator import Rss201rev2Feed

from coltrane.content_loaders import load_posts


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
        return None
