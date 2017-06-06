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
from django.contrib.sitemaps import views as sitemap_views
from django.views.static import serve as static_serve
from wxwtf.flushots import views as flushots_views
from wxwtf.random_oscars_ballot import views as random_oscars_ballot_views
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import RedirectView, ListView
from toolbox.views import DirectTemplateView
from toolbox import views as toolbox_views
admin.autodiscover()


# Redirects from the old Wordpress URL structure to the new Django one.
urlpatterns = [
    # Redirect links to old blog to new posts
    url(r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$',
        RedirectView.as_view(url='/posts/%(year)s/%(month)s/%(day)s/%(slug)s/')
    ),
    # Redirects old tag pages
    url(r'^tag/(?P<tag>[^/]+)/$', RedirectView.as_view(url='/who-is-ben-welsh/')),
    url(r'^tags/(?P<tag>[^/]+)/$', RedirectView.as_view(url='/who-is-ben-welsh/')),
    # Redirects old feeds to new feeds
    url(r'^comments/feed/$', RedirectView.as_view(url='/feeds/comments/')),
    url(r'^feed/$', RedirectView.as_view(url='/feeds/posts/')),
    url(r'^feed/atom/$', RedirectView.as_view(url='/feeds/posts/')),
    url(r'^feed/rss/$', RedirectView.as_view(url='/feeds/posts/')),
    # Redirects from old flatpages
    url(r'^bio/$', RedirectView.as_view(url='/who-is-ben-welsh/')),
    url(r'^work/$', RedirectView.as_view(url='/who-is-ben-welsh/')),
    # Scrape pages from tutorial on old site.
    url(r'^scrape/albums/2006.html$', DirectTemplateView.as_view(
        template_name='tutorials/scrape/2006.html')),
    url(r'^scrape/albums/2007.html$', DirectTemplateView.as_view(
        template_name='tutorials/scrape/2007.html')),
    # OpenLayers tutorial on old site.
    url('^openlayers-proportional-symbols/$', DirectTemplateView.as_view(
        template_name='tutorials/openlayers-proportional-symbols/index.html')),
    # DC Music Stores map from old site.
    url(r'^music/$', RedirectView.as_view(url='/')),
    # Arcade Fire hypecloud from old site.
    url(r'^hypecloud/$', RedirectView.as_view(url='/')),
    # DC Happy hours from old site.
    url(r'^happyhours/$', RedirectView.as_view(url='/')),
    url(r'^happyhours/(?P<whatever>.*)', RedirectView.as_view(url='/')),
    # Redirect old images from legacy site
    url(r'^images/(?P<file_name>[^/]+)$', RedirectView.as_view(
        url='/media/img/%(file_name)s')),
    # Longer apps urls
    url(r'^applications/$', RedirectView.as_view(url='/apps/')),
    url(r'^applications/(?P<anything>.*)/$', RedirectView.as_view(
        url='/apps/%(anything)s/')),
    # V2 of the blog, now replaced by the consolidated ticker
    url(r'^books/$', RedirectView.as_view(url='/ticker/?filters=book'),
        name='coltrane_book_root'),
    url(r'^books/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=book'), name='coltrane_book_list'),
    url(r'^comments/$', RedirectView.as_view(url='/ticker/?filters=comment'),
        name='coltrane_comment_root'),
    url(r'^comments/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=comment'), name='coltrane_comment_list'),
    url(r'^commits/$', RedirectView.as_view(url='/ticker/?filters=commit'),
        name='coltrane_commit_root'),
    url(r'^commits/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=commit'), name='coltrane_commit_list'),
    url(r'^corrections/$', RedirectView.as_view(url='/ticker/?filters=change'),
        name='coltrane_correx_root'),
    url(r'^corrections/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=change'), name='coltrane_correx_list'),
    url(r'^links/$', RedirectView.as_view(url='/ticker/?filters=link'),
        name='coltrane_link_root'),
    url(r'^links/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=link'), name='coltrane_link_list'),
    url(r'^locations/$', RedirectView.as_view(url='/ticker/?filters=location'),
        name='coltrane_location_root'),
    url(r'^locations/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=location'), name='coltrane_location_list'),
    url(r'^movies/$', RedirectView.as_view(url='/ticker/?filters=movie'),
        name='coltrane_movie_root'),
    url(r'^movies/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=movie'), name='coltrane_movie_list'),
    url(r'^photos/$', RedirectView.as_view(url='/ticker/?filters=photo'),
        name='coltrane_photo_root'),
    url(r'^photos/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=photo'), name='coltrane_photo_list'),
    url(r'^shouts/$', RedirectView.as_view(url='/ticker/?filters=shout'),
        name='coltrane_shout_root'),
    url(r'^shouts/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=shout'), name='coltrane_link_list'),
    url(r'^tracks/$', RedirectView.as_view(url='/ticker/?filters=track'),
        name='coltrane_track_root'),
    url(r'^tracks/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=track'), name='coltrane_track_list'),
    url(r'^categories/list/$', RedirectView.as_view(url='/ticker/'),
        name='coltrane_category_list'),
    url(r'^apps/page/(?P<page>[0-9]+)/$', RedirectView.as_view(url='/apps/'),
        name='coltrane_app_root'),
    url(r'^posts/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/posts/'), name='coltrane_post_archive_index'),
    url(r'^ticker/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/'), name='coltrane_ticker_root'),
]

# URLs for the new blog
urlpatterns += [

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
    url(r'^apps/$', DirectTemplateView.as_view(**{
            'template_name': 'coltrane/app_list.html',
            'extra_context': {
                'app_list': bona_fides.APP_LIST,
            }
        }), name='coltrane_app_list'),
    url(r'^clips/$', DirectTemplateView.as_view(**{
            'template_name': 'coltrane/clip_list.html',
            'extra_context': {
                'clip_list': bona_fides.CLIP_LIST,
            }
        }), name='coltrane_clip_list'),
    url(r'^talks/$', DirectTemplateView.as_view(
        **{ 'template_name': 'coltrane/talk_list.html' }),
        name='coltrane_talk_list'),
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
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', static_serve,
            {'document_root': settings.STATIC_ROOT, 'show_indexes': True, }),
        url(r'^static/(?P<path>.*)$', static_serve, {
            'document_root': settings.STATIC_ROOT,
            'show_indexes': True,
        }),
        url(r'^500/$', views.server_error),
    ]
else:
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', RedirectView.as_view(
             url='http://palewire.s3.amazonaws.com/%(path)s')),
        url(r'^static/(?P<path>.*)$', RedirectView.as_view(
             url='http://palewire.s3.amazonaws.com/%(path)s')),
    ]

if settings.PRODUCTION:
    urlpatterns += [
        url(r'^app_status/$', toolbox_views.app_status, name='status'),
    ]


# 500 page fix
handler500 = 'coltrane.views.server_error'
