from django.conf.urls.defaults import *

# Models
from coltrane.models import Post, Link
from tagging.models import Tag, TaggedItem

# Utils
from coltrane.utils.cloud import calculate_cloud

urlpatterns = patterns('',
	
	# List
	url(r'^$', 'django.views.generic.list_detail.object_list', { 
			'queryset': Tag.objects.all(),
			'template_name': 'coltrane/tag_list.html',
			'extra_context': {'tag_cloud': calculate_cloud(TaggedItem.objects.select_related().all(), steps=6)[:100]}
		}, name='coltrane_tag_list'),
		
	# Detail
	url(r'^(?P<tag>[^/]+)/$', 'coltrane.views.tag_detail', name='coltrane_tag_detail'),

)

"""
[217.66666666666666, 434.33333333333331, 651.0, 867.66666666666663, 1084.3333333333333, 1301.0]

"""
