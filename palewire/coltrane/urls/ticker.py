from django.conf.urls.defaults import *

from coltrane.models import Ticker

urlpatterns = patterns('django.views.generic',
	
	# The root url
	url(r'^$', 'simple.redirect_to', { 'url': '/ticker/page/1/' }, name='coltrane_ticker_root'),
	
	# Pagination
	url(r'^page/(?P<page>[0-9]+)/$', 'list_detail.object_list', { 
		'queryset': Ticker.objects.all().order_by('-pub_date'),
		'paginate_by': 20,
		}, name='coltrane_ticker_list'),

)