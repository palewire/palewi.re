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
	url(r'^page/(?P<page>[0-9]+)/$', 'object_list', entry_index_dict, name='coltrane_post_archive_index'),
	
)

urlpatterns += patterns('',
	url(r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$', 
		'coltrane.views.post_detail', name='coltrane_post_detail'),
)