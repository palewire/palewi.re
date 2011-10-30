from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'nicar.polls.views.index'),
    url(r'^(?P<poll_id>\d+)/$', 'nicar.polls.views.detail'),
    url(r'^(?P<poll_id>\d+)/vote/$', 'nicar.polls.views.vote'),
)
