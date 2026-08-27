import datetime

from django.contrib import sitemaps as django_sitemaps

from coltrane.content_loaders import MarkdownPost, load_posts


class AbstractSitemapClass:
    url = None

    def get_absolute_url(self):
        return self.url


class StaticSitemap(django_sitemaps.Sitemap):
    pages = {
        "bio": "/who-is-ben-welsh/",
        "clips": "/clips/",
        "apps": "/apps/",
        "code": "/code/",
        "guides": "/guides/",
        "posts": "/posts/",
        "talks": "/talks/",
    }
    main_sitemaps = []
    for page in pages.keys():
        sitemap_class = AbstractSitemapClass()
        sitemap_class.url = pages[page]
        main_sitemaps.append(sitemap_class)

    def items(self):
        return self.main_sitemaps


class PostsSitemap(django_sitemaps.Sitemap):
    priority = 0.9

    def items(self) -> list[MarkdownPost]:
        return load_posts()

    def lastmod(self, item: MarkdownPost) -> datetime.date:
        return item.published_at.date()

    def location(self, item: MarkdownPost) -> str:
        return item.get_absolute_url()


sitemaps = {
    "static": StaticSitemap,
    "posts": PostsSitemap,
}
