from django.contrib.syndication.views import Feed
from django.urls import reverse
from coltrane.models import Post


class LatestPostsFeed(Feed):
    title = "palewi.re posts"
    link = "/feeds/posts/"
    description = "the latest"

    def items(self):
        return Post.live.all().order_by("-pub_date")[:10]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return None
