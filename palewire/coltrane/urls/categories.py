from django.conf.urls.defaults import *

from coltrane.models import Category

index_dict = {
	'queryset': Category.objects.all(),
}

urlpatterns = patterns('django.views.generic.list_detail',
	url(r'list/$', 'object_list', index_dict, name="coltrane_category_list"),
)

urlpatterns += patterns('',
	url(r'(?P<slug>[-\w]+)/$', 'coltrane.views.category_detail', name="coltrane_category_detail"),
)



