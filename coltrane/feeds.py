from django.contrib.syndication.views import Feed

from coltrane.content_loaders import load_posts


class LatestPostsFeed(Feed):
    title = "palewi.re posts"
    link = "/feeds/posts/"
    description = "the latest"

    def items(self):
        return load_posts()[:10]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return None
