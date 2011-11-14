from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'nicar.flu_map.views.index'),
)
