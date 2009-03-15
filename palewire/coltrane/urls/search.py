from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',               
    url(r'^$', 'solango.views.select', {'template_name': 'coltrane/search.html'}, 'solango_search'),
    url(r'^search-error/$', direct_to_template, {'template': 'solango/error.html'}, 'solango_search_error'),    
)
