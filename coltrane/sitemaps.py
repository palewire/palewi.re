from coltrane.models import Post
from django.contrib import sitemaps
from django.contrib.sitemaps import GenericSitemap

post_dict = {
    'queryset': Post.live.all(),
    'date_field': 'pub_date',
}

class AbstractSitemapClass(object):
    url = None

    def get_absolute_url(self):
        return self.url


class StaticSitemap(sitemaps.Sitemap):
    pages = {
        'bio':'/who-is-ben-welsh/',
        'clips': '/clips/',
        'posts': '/posts/',
        'talks': '/talks/',
    }
    main_sitemaps = []
    for page in pages.keys():
        sitemap_class = AbstractSitemapClass()
        sitemap_class.url = pages[page]
        main_sitemaps.append(sitemap_class)

    def items(self):
        return self.main_sitemaps


sitemaps = {
    'static': StaticSitemap,
    'posts': GenericSitemap(post_dict, priority=0.9),
}
