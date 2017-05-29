from django.conf.urls import include, url
from nicar.flu_map import views


urlpatterns = [
    url(r'^$', views.index),
]
