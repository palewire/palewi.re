from django.conf.urls.defaults import *

from coltrane.models import Link

index_dict = {
	'queryset': Link.objects.all().order_by("-pub_date"),
	'paginate_by': 25,
}

info_dict = {
	'queryset': Link.objects.all(),
	'date_field': 'pub_date',
	'month_format': '%m',
}

urlpatterns = patterns('django.views.generic',
	url(r'^page/(?P<page>[0-9]+)/$', 'list_detail.object_list', index_dict, name='coltrane_link_list'),
	url(r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$', 
		'date_based.object_detail', info_dict, name='coltrane_link_detail'),
)






