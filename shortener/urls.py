from django.conf.urls.defaults import *

urlpatterns = patterns("shortener.views",
    (r'^$', 'index'),
    (r'^submit/$', 'submit'),
    (r'^(?P<base62_id>\w+)$', 'follow'),
    (r'^info/(?P<base62_id>\w+)$', 'info'),
)
