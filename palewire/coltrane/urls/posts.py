from django.conf.urls.defaults import *

from coltrane.models import Post

entry_index_dict = {
	'queryset': Post.live.all().order_by("-pub_date"),
	#'paginate_by': 25,
}

entry_info_dict = {
	'queryset': Post.live.all(),
	'date_field': 'pub_date',
	'month_format': '%m',
}

urlpatterns = patterns('django.views.generic.list_detail',
	(r'^page/(?P<page>[0-9]+)/$', 'object_list', entry_index_dict, 'coltrane_post_archive_index'),
	
)

urlpatterns += patterns('django.views.generic.date_based',
	(r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$', 
		'object_detail', entry_info_dict, 'coltrane_post_detail'),
)