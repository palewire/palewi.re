from django.conf.urls.defaults import *


urlpatterns = patterns('django.views.generic.simple',
	
	# The root url
	url(r'^$', 'redirect_to', { 'url': '/applications/page/1/' }, name='coltrane_app_root'),

	# List
	url(r'^page/(?P<page>[0-9]+)/$', 'direct_to_template', { 
			'template': 'coltrane/app_list.html',
		}, name='coltrane_app_list'),

)