from django.conf.urls.defaults import *
from coltrane import views

urlpatterns = patterns('django.views.generic.simple',
    
    # The root url
    url(r'^$', 'direct_to_template', { 
            'template': 'coltrane/app_list.html',
        }, name='coltrane_app_list'),
    
    # Old page redirect
    url(r'^page/(?P<page>[0-9]+)/$', 'redirect_to', { 'url': '/applications/' },
        name='coltrane_app_root'),
    
    # newtwitter style autopagination with django
    url(r'^twitter-style-infinite-scroll-with-django-demo/$',
        views.newtwitter_pagination_index,
        name='coltrane_app_newtwitter_index'),
    
    url(r'^twitter-style-infinite-scroll-with-django-demo/json/(?P<page>[0-9]+)/',
        views.newtwitter_pagination_json,
        name='coltrane_app_newtwitter_json'),

    # BRING THE NEWS BACK
    url(r'^bring-the-news-back/$',
        'direct_to_template', {'template': 'bring_the_news_back/index.html' },
        name='coltrane_app_newtwitter_json'),

)

