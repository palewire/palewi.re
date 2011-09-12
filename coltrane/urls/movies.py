from django.conf.urls.defaults import *

# Models
from coltrane.models import Movie

index_dict = {
    'queryset': Movie.objects.all().order_by("-pub_date"),
    'paginate_by': 25,
}

urlpatterns = patterns('django.views.generic',

    # The root url
    url(r'^$', 'simple.redirect_to', { 'url': '/movies/page/1/' }, name='coltrane_movie_root'),
    
    # Pagination
    #url(r'^page/(?P<page>[0-9]+)/$', 'list_detail.object_list', index_dict, name='coltrane_movie_list'),
    url(r'^page/(?P<page>[0-9]+)/$', 'simple.redirect_to', { 'url': '/ticker/page/1/' },
        name='coltrane_movie_list'),
)






