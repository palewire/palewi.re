from django.conf.urls import include, url
from wxwtf.kennedy import views


urlpatterns = [
    url(r'^$', views.index, name='kennedy_index'),
]
