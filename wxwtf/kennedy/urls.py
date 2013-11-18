from django.conf.urls import patterns, include, url

urlpatterns = patterns('wxwtf.kennedy.views',
    url(r'^$', 'index', name='kennedy_index'),
)
