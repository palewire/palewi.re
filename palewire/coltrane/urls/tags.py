from django.conf.urls.defaults import *

from coltrane.models import  Post, Link
from tagging.models import Tag

urlpatterns = patterns('',
	(r'^$', 'django.views.generic.list_detail.object_list',{ 
			'queryset': Tag.objects.all(),
			'template_name': 'coltrane/tag_list.html' 
		}, 'coltrane_tag_list'),
	(r'(?P<slug>[-\w]+)/$', 'cms.coltrane.views.tag_detail'),
)