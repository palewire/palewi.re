from django.conf.urls.defaults import *

from coltrane.models import Ticker

urlpatterns = patterns('django.views.generic',
	
	# The root url
	url(r'^$', 'simple.redirect_to', { 'url': '/ticker/page/1/' }, name='coltrane_ticker_root'),

)