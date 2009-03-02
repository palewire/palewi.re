from django.conf.urls.defaults import *

from coltrane.models import Tumbler

urlpatterns = patterns('',
	(r'^$', 
		'django.views.generic.list_detail.object_list',
		{ 'queryset': Tumbler.objects.all().order_by('-pub_date')[:50] }, 'coltrane_tumbler_list'),
	(r'^page/(?P<page>[0-9]+)/$', 
		'django.views.generic.list_detail.object_list',
		{ 
			'queryset': Tumbler.objects.all().order_by('-pub_date'),
			'paginate_by': 20,
		}, 'coltrane_tumbler_paginated_list'),
)