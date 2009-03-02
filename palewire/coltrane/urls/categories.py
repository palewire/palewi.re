from django.conf.urls.defaults import *

from coltrane.models import Category

index_dict = {
	'queryset': Category.objects.all(),
}

urlpatterns = patterns('django.views.generic.list_detail',
	(r'list/$', 'object_list', index_dict, 'coltrane_category_list'),
)

urlpatterns += patterns('',
	(r'(?P<slug>[-\w]+)/$', 'cms.coltrane.views.category_detail'),
)



