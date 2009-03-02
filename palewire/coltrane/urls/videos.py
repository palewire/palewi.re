from django.conf.urls.defaults import *

from coltrane.models import Video

index_dict = {
	'queryset': Video.objects.all().order_by("-pub_date"),
	'paginate_by': 25,
}

info_dict = {
	'queryset': Video.objects.all(),
	'date_field': 'pub_date',
	'month_format': '%m',
}

urlpatterns = patterns('django.views.generic',
	(r'^page/(?P<page>[0-9]+)/$', 'list_detail.object_list', index_dict, 'coltrane_video_list'),
	(r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$', 
		'date_based.object_detail', info_dict, 'coltrane_video_detail'),
		
)




