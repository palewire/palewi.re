from coltrane.models import Post, Category
from django.contrib.sitemaps import GenericSitemap, Sitemap

post_dict = {
    'queryset': Post.live.all(),
    'date_field': 'pub_date',
}

category_dict = {
    'queryset': Category.live.all(),
}

class AbstractSitemapClass(object):
    url = None
    
    def get_absolute_url(self):
        return self.url


class StaticSitemap(Sitemap):
    pages = {
        'bio':'/who-is-ben-welsh/',
        'colophon':'/colophon/',
        'feeds': '/feeds/list/',
        'apps': '/apps/',
        'clips': '/clips/',
        'posts': '/posts/',
        'talks': '/talks/',
        'ticker': '/ticker/',
        'bring-the-news-back': '/apps/bring-the-news-back/',
        'kennedy-name-generator': '/kennedy/',
        'random-oscars-ballot': '/apps/random-oscars-ballot/',
        'return-of-the-mack-ringtone': '/mack/',
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
    'categories': GenericSitemap(category_dict, priority=0.6),
}
