from django.conf.urls import include, url
from nicar.polls import views


urlpatterns = [
    url(r'^$', views.index),
    url(r'^(?P<poll_id>\d+)/$', views.detail),
    url(r'^(?P<poll_id>\d+)/vote/$', views.vote),
]
