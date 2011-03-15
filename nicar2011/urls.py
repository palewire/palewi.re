from django.conf.urls.defaults import *
from django.conf import settings


urlpatterns = patterns('nicar2011.views',
    (r'^$', 'index'),
    (r'^(?P<poll_id>\d+)/$', 'detail'),
    (r'^(?P<poll_id>\d+)/vote/$', 'vote'),
    (r'^(?P<poll_id>\d+)/data.xml$', 'data'),
    (r'^crossdomain.xml$', 'crossdomain'),
)
