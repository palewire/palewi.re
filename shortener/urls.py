from django.conf.urls import patterns, include, url

urlpatterns = patterns("shortener.views",
    url(r'^$', 'index', name="shortener-index"),
    url(r'^submit/$', 'submit', name="shortener-submit"),
    url(r'^(?P<base62_id>\w+)$', 'follow'),
)
