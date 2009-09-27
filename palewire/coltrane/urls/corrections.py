from django.conf.urls.defaults import *

# Models
#from coltrane.models import Link
from correx.models import Change

index_dict = {
	'queryset': Change.objects.live().order_by("-pub_date"),
	'paginate_by': 25,
}

urlpatterns = patterns('django.views.generic',

	# The root url
	url(r'^$', 'simple.redirect_to', { 'url': '/corrections/page/1/' }, name='coltrane_correx_root'),
	
	# Pagination
	url(r'^page/(?P<page>[0-9]+)/$', 'list_detail.object_list', index_dict, name='coltrane_correx_list'),
	
)

urlpatterns += patterns('coltrane.views',

	# Redirect the absolute_url from the ticker to the content object 
	# page where the correction can be found...
	url(r'^(?P<id>[0-9]+)/$', 'correx_redirect', name='coltrane_correx_redirect'),

)






