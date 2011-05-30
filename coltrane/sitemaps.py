# Sitemaps
from django.contrib.sitemaps import GenericSitemap, Sitemap

# Models
from coltrane.models import *

post_dict = {
    'queryset': Post.live.all(),
    'date_field': 'pub_date',
}

category_dict = {'queryset': Category.live.all(),}

sitemaps = {
    'posts': GenericSitemap(post_dict, priority=0.9),
    'categories': GenericSitemap(category_dict, priority=0.6),
}
