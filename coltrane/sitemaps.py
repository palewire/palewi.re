# Sitemaps
from django.contrib.sitemaps import FlatPageSitemap, GenericSitemap, Sitemap

# Models
from coltrane.models import *
from tagging.models import Tag

post_dict = {
    'queryset': Post.live.all(),
    'date_field': 'pub_date',
}

tag_dict = {'queryset': Tag.objects.all(),}
category_dict = {'queryset': Category.live.all(),}

class TagSitemap(Sitemap):
    priority = 0.6

    def items(self):
        return Tag.objects.all()

    def location(self, obj):
        return u'/tags/%s' % obj

sitemaps = {
    'about': FlatPageSitemap,
    'posts': GenericSitemap(post_dict, priority=0.9),
    'categories': GenericSitemap(category_dict, priority=0.6),
    'tags': TagSitemap
}
