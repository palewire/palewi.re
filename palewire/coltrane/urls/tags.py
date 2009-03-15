from django.conf.urls.defaults import *

from coltrane.models import  Post, Link
from tagging.models import Tag

urlpatterns = patterns('',
	url(r'^$', 'django.views.generic.list_detail.object_list',{ 
			'queryset': Tag.objects.all(),
			'template_name': 'coltrane/tag_list.html' 
		}, name='coltrane_tag_list'),
	url(r'^(?P<tag>[^/]+)/$', 'coltrane.views.tag_detail', name='coltrane_tag_detail'),
)