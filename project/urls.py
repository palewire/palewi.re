import os
this_dir = os.path.dirname(__file__)

from django.conf.urls import include, url
from django.conf import settings
from django.contrib import admin
import bona_fides
from coltrane import feeds
from coltrane import views
from coltrane.models import Post
from coltrane.sitemaps import sitemaps
from bona_fides.models import Clip, Talk
from redirects import patterns as redirectpatterns
from django.contrib.sitemaps import views as sitemap_views
from django.views.static import serve as static_serve
from wxwtf.flushots import views as flushots_views
from wxwtf.random_oscars_ballot import views as random_oscars_ballot_views
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import RedirectView, ListView
from toolbox.views import DirectTemplateView
from toolbox import views as toolbox_views
admin.autodiscover()


# URLs for the blog
blogpatterns = [

    # The index
    url(r'^$', views.index, name='coltrane_index'),
    # My bio
    url(r'^who-is-ben-welsh/$', views.bio, name="coltrane_bio"),
    # About the site
    url(r'^colophon/$', DirectTemplateView.as_view(
        **{'template_name': 'coltrane/colophon.html'}),
        name="coltrane_colophon"),
    # The admin
    url(r'^admin/', include(admin.site.urls)),
    # Main list pages
    url(r'^work/$', DirectTemplateView.as_view(**{
            'template_name': 'coltrane/work_list.html',
            'extra_context': {
                'object_list': Clip.objects.all(),
            }
        }), name='coltrane_work_list'),
    url(r'^talks/$', DirectTemplateView.as_view(**{
            'template_name': 'coltrane/talk_list.html',
            'extra_context': {
                'object_list': Talk.objects.all(),
            }
        }), name='coltrane_talk_list'),
    url(r'^posts/$', ListView.as_view(
        queryset=Post.live.all().order_by("-pub_date")),
        name='coltrane_post_list'),
    url(r'^ticker/$', views.ticker_detail,
        name='coltrane_ticker_list'),
    url(r'^ticker/page/(?P<page>[0-9]+).json$', views.ticker_detail,
        {'response_type': 'json'},
        name='coltrane_ticker_json'),
    # Detail pages
    url(r'^posts/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$',
        views.post_detail, name='coltrane_post_detail'),
    url(r'categories/(?P<slug>[-\w]+)/$', views.category_detail,
        name="coltrane_category_detail"),
    url(r'^corrections/(?P<id>[0-9]+)/$', views.correx_redirect,
        name='coltrane_correx_redirect'),
    # Feeds
    url(r'^feeds/list/$', DirectTemplateView.as_view(
        **{'template_name': 'coltrane/feed_list.html'})),

    url(r'feeds/the-full-feed/$', feeds.FullFeed(), name="feeds-the-full-feed"),
    url(r'feeds/less-noise/$', feeds.LessNoise(), name="feeds-less-noise"),
    url(r'feeds/beers/$', feeds.RecentBeers(), name="feeds-beers"),
    url(r'feeds/posts/$', feeds.RecentPosts(), name="feeds-posts"),
    url(r'feeds/comments/$', feeds.RecentComments(), name="feeds-comments"),
    url(r'feeds/shouts/$', feeds.RecentShouts(), name="feeds-shouts"),
    url(r'feeds/links/$', feeds.RecentLinks(), name="feeds-links"),
    url(r'feeds/photos/$', feeds.RecentPhotos(), name="feeds-photos"),
    url(r'feeds/tracks/$', feeds.RecentTracks(), name="feeds-tracks"),
    url(r'feeds/books/$', feeds.RecentBooks(), name="feeds-books"),
    url(r'feeds/commits/$', feeds.RecentCommits(), name="feeds-commits"),
    url(r'feeds/category/(?P<slug>[-\w]+)/$', feeds.CategoryFeed(), name="feeds-category"),
    url(r'feeds/corrections/$', feeds.RecentCorrections(), name="feeds-corrections"),
    url(r'feeds/movies/$', feeds.RecentMovies(), name="feeds-movies"),
    url(r'feeds/locations/$', feeds.RecentLocations(), name="feeds-locations"),
    url(r'feeds/questionheds/$', feeds.RecentHeds(), name="feeds-questionheds"),

    # Sitemaps
    url(r'^sitemap\.xml$', sitemap_views.index,
        {'sitemaps': sitemaps},),
    url(r'^sitemap-(?P<section>.+)\.xml$', sitemap_views.sitemap,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap'),

    # Robots and favicon
    url(r'^robots\.txt$', DirectTemplateView.as_view(
        **{'template_name': 'robots.txt', 'content_type': 'text/plain'}), name='robots'),
    url(r'^favicon.ico$', RedirectView.as_view(
        url='http://palewire.s3.amazonaws.com/favicon.ico')),

    # Kennedy name generator
    url(r'^kennedy/', include('wxwtf.kennedy.urls')),

    # Flu Shots 2011
    url(r'free-flu-shots/$', flushots_views.index, name='flushots-index'),

    # Random Oscars Ballot
    url(r'random-oscars-ballot/$', random_oscars_ballot_views.index,
        name='random-oscars-ballot-index'),

    # newtwitter style autopagination with django
    url(r'^apps/twitter-style-infinite-scroll-with-django-demo/$',
        views.newtwitter_pagination_index,
        name='coltrane_app_newtwitter_index'),
    url(r'^apps/twitter-style-infinite-scroll-with-django-demo/json/(?P<page>[0-9]+)/',
        views.newtwitter_pagination_json,
        name='coltrane_app_newtwitter_json'),

    # BRING THE NEWS BACK
    url(r'^apps/bring-the-news-back/$', DirectTemplateView.as_view(
        **{'template_name': 'wxwtf/bring_the_news_back/index.html' }),
        name='coltrane_app_newtwitter_json'),

    # Return of the Mack ringtone
    url(r'^mack/$', DirectTemplateView.as_view(**{'template_name': 'wxwtf/mack.html'}),
        name='mack'),

    # Candy says...
    url(r'^candysays/$', DirectTemplateView.as_view(**{
        'template_name': 'wxwtf/candy.html'}),
        name='candy-says'),

    # Where will the Regional Connector go?
    url(r'^regional-connector/$', DirectTemplateView.as_view(
        **{'template_name': 'wxwtf/regional_connector/index.html'}),
        name='candy-says'),

    # Other weird stuff
    url(r'^comments/', include('django_comments.urls')),
    url(r'^correx/', include('correx.urls')),
    url(r'^nicar/polls/', include("nicar.polls.urls")),
    url(r'^nicar/flu-map/', include("nicar.flu_map.urls")),
]

if settings.DEBUG:
    blogpatterns += [
        url(r'^media/(?P<path>.*)$', static_serve,
            {'document_root': settings.STATIC_ROOT, 'show_indexes': True, }),
        url(r'^static/(?P<path>.*)$', static_serve, {
            'document_root': settings.STATIC_ROOT,
            'show_indexes': True,
        }),
        url(r'^500/$', views.server_error),
    ]
else:
    blogpatterns += [
        url(r'^media/(?P<path>.*)$', RedirectView.as_view(
             url='http://palewire.s3.amazonaws.com/%(path)s')),
        url(r'^static/(?P<path>.*)$', RedirectView.as_view(
             url='http://palewire.s3.amazonaws.com/%(path)s')),
    ]

if settings.PRODUCTION:
    blogpatterns += [
        url(r'^app_status/$', toolbox_views.app_status, name='status'),
    ]

# Combine patterns
urlpatterns = redirectpatterns
urlpatterns += blogpatterns


# 500 page fix
handler500 = 'coltrane.views.server_error'
