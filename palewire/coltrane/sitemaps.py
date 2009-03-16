from django.contrib.sitemaps import FlatPageSitemap, GenericSitemap, Sitemap
from coltrane.models import *
from tagging.models import Tag

post_dict = {
	'queryset': Post.live.all(),
	'date_field': 'pub_date',
}

shout_dict = {
	'queryset': Shout.objects.all(),
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
	'shouts': GenericSitemap(shout_dict, priority=0.8),
	'categories': GenericSitemap(category_dict, priority=0.6),
	'tags': TagSitemap
}
