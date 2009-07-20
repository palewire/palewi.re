from django.conf.urls.defaults import *

from coltrane.models import Ticker

urlpatterns = patterns('django.views.generic',
	
	# The root url
	url(r'^$', 'simple.direct_to_template', { 'template': 'coltrane/index.html' }, name='coltrane_index'),

)