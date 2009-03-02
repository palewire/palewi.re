from django.conf.urls.defaults import *

from coltrane.models import Track

index_dict = {
	'queryset': Track.objects.all().order_by("-pub_date"),
	'paginate_by': 25,
}

urlpatterns = patterns('django.views.generic.list_detail',
	(r'^page/(?P<page>[0-9]+)/$', 'object_list', index_dict, 'coltrane_track_list'),
)


