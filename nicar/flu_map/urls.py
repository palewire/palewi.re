from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'nicar.flu_map.views.index'),
)
