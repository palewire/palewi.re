from django.conf.urls.defaults import *

from coltrane.models import Ticker

urlpatterns = patterns('',
	url(r'^$', 
		'django.views.generic.list_detail.object_list',
		{ 
			'queryset': Ticker.objects.all().order_by('-pub_date')[:50],
		}, name='coltrane_ticker_list'),
	url(r'^page/(?P<page>[0-9]+)/$', 
		'django.views.generic.list_detail.object_list',
		{ 
			'queryset': Ticker.objects.all().order_by('-pub_date'),
			'paginate_by': 20,
		}, name='coltrane_ticker_paginated_list'),
)