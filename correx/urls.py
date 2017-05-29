from django.conf.urls import include, url
from correx import views


urlpatterns = [
    url(r'^admin/filter/contenttype/$', views.filter_contenttypes_by_app,
        name="filter-contenttypes-by-app"),
]
