from django.conf.urls.defaults import *

# Models
from tagging.models import Tag
from coltrane.models import TopTag


urlpatterns = patterns('',
    
    # List
    url(r'^$', 'django.views.generic.list_detail.object_list', { 
            'queryset': Tag.objects.all(),
            'template_name': 'coltrane/tag_list.html',
            'extra_context': {'tag_cloud': TopTag.objects.all()}
        }, name='coltrane_tag_list'),
        
    # Detail
    url(r'^(?P<tag>[^/]+)/$', 'coltrane.views.tag_detail', name='coltrane_tag_detail'),

)
