from django.conf.urls.defaults import *

from coltrane.models import Track

index_dict = {
    'queryset': Track.objects.all().order_by("-pub_date"),
    'paginate_by': 25,
}

urlpatterns = patterns('django.views.generic',
    
    # The root url
    url(r'^$', 'simple.redirect_to', { 'url': '/tracks/page/1/' }, name='coltrane_track_root'),
    
    # List
    # url(r'^page/(?P<page>[0-9]+)/$', 'list_detail.object_list', index_dict, name='coltrane_track_list'),
    url(r'^page/(?P<page>[0-9]+)/$', 'simple.redirect_to', { 'url': '/ticker/page/1/' },
        name='coltrane_track_list'),

)


