from django.conf.urls import patterns, include, url

urlpatterns = patterns("shortener.views",
    (r'^$', 'index'),
    (r'^submit/$', 'submit'),
    (r'^(?P<base62_id>\w+)$', 'follow'),
)
