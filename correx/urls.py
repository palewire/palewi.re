from django.conf.urls import patterns, include, url

urlpatterns = patterns('correx.views',
    url(r'^admin/filter/contenttype/$', 'filter_contenttypes_by_app',
        name="filter-contenttypes-by-app"),
)
