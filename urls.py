import os
this_dir = os.path.dirname(__file__)

from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
admin.autodiscover()
import bona_fides
from coltrane import feeds
from coltrane.models import Post
from coltrane.sitemaps import sitemaps
from django.views.static import serve as static_serve
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic.simple import direct_to_template, redirect_to


# Redirects from the old Wordpress URL structure to the new Django one.
urlpatterns = patterns('django.views.generic.simple',
    # Redirect links to old blog to new posts
    (r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$', 'redirect_to', 
        {'url': '/posts/%(year)s/%(month)s/%(day)s/%(slug)s/'}
    ),
    # Redirects old tag pages to the new tag pages
    (r'^tag/(?P<tag>[^/]+)/$', 'redirect_to', {'url': '/tags/%(tag)s/'}),
    # Redirects old feeds to new feeds
    (r'^comments/feed/$', 'redirect_to', {'url': '/feeds/comments/'}),
    (r'^feed/$', 'redirect_to', {'url': '/feeds/posts/'}),
    (r'^feed/atom/$', 'redirect_to', {'url': '/feeds/posts/'}),
    (r'^feed/rss/$', 'redirect_to', {'url': '/feeds/posts/'}),
    # Redirects from old flatpages
    (r'^bio/$', 'redirect_to', {'url': '/who-is-ben-welsh/'}),
    (r'^work/$', 'redirect_to', {'url': '/who-is-ben-welsh/'}),
    # Scrape pages from tutorial on old site.
    (r'^scrape/albums/2006.html$', 'direct_to_template',
        {'template': 'tutorials/scrape/2006.html'}),
    (r'^scrape/albums/2007.html$', 'direct_to_template',
        {'template': 'tutorials/scrape/2007.html'}),
    # OpenLayers tutorial on old site.
    ('^openlayers-proportional-symbols/$', 'direct_to_template',
        {'template': 'tutorials/openlayers-proportional-symbols/index.html'}),
    # DC Music Stores map from old site.
    (r'^music/$', 'redirect_to', {'url': '/'}),
    # Arcade Fire hypecloud from old site.
    (r'^hypecloud/$', 'redirect_to', {'url': '/'}),
    # DC Happy hours from old site.
    (r'^happyhours/$', 'redirect_to', {'url': '/'}),
    (r'^happyhours/(?P<whatever>.*)', 'redirect_to', {'url': '/'}),
    # Redirect old images from legacy site
    (r'^images/(?P<file_name>[^/]+)$', 'redirect_to', {'url': '/media/img/%(file_name)s'}),
    # Longer apps urls
    (r'^applications/$', 'redirect_to', {'url': '/apps/'}),
    (r'^applications/(?P<anything>.*)/$', 'redirect_to', 
        {'url': '/apps/%(anything)s/'}
    ),
    # V2 of the blog, now replaced by the consolidated ticker
    url(r'^books/$', 'redirect_to', 
        { 'url': '/ticker/?filters=book' },
        name='coltrane_book_root'),
    url(r'^books/page/(?P<page>[0-9]+)/$', 'redirect_to', 
        { 'url': '/ticker/?filters=book' },
        name='coltrane_book_list'),
    url(r'^comments/$', 'redirect_to', 
        { 'url': '/ticker/?filters=comment' },
        name='coltrane_comment_root'),
    url(r'^comments/page/(?P<page>[0-9]+)/$', 'redirect_to', 
        { 'url': '/ticker/?filters=comment' }, 
        name='coltrane_comment_list'),
    url(r'^commits/$', 'redirect_to', 
        { 'url': '/ticker/?filters=commit' }, 
        name='coltrane_commit_root'),
    url(r'^commits/page/(?P<page>[0-9]+)/$', 'redirect_to',
        { 'url': '/ticker/?filters=commit' },
        name='coltrane_commit_list'),
    url(r'^corrections/$', 'redirect_to',
        { 'url': '/ticker/?filters=change' },
        name='coltrane_correx_root'),
    url(r'^corrections/page/(?P<page>[0-9]+)/$', 'redirect_to',
        { 'url': '/ticker/?filters=change' },
        name='coltrane_correx_list'),
    url(r'^links/$', 'redirect_to',
        { 'url': '/ticker/?filters=link' },
        name='coltrane_link_root'),
    url(r'^links/page/(?P<page>[0-9]+)/$', 'redirect_to',
        { 'url': '/ticker/?filters=link' },
        name='coltrane_link_list'),
    url(r'^locations/$', 'redirect_to',
        { 'url': '/ticker/?filters=location' },
        name='coltrane_location_root'),
    url(r'^locations/page/(?P<page>[0-9]+)/$', 'redirect_to',
        { 'url': '/ticker/?filters=location' },
        name='coltrane_location_list'),
    url(r'^movies/$', 'redirect_to',
        { 'url': '/ticker/?filters=movie' },
        name='coltrane_movie_root'),
    url(r'^movies/page/(?P<page>[0-9]+)/$', 'redirect_to',
        { 'url': '/ticker/?filters=movie' },
        name='coltrane_movie_list'),
    url(r'^photos/$', 'redirect_to',
        { 'url': '/ticker/?filters=photo', },
        name='coltrane_photo_root'),
    url(r'^photos/page/(?P<page>[0-9]+)/$', 'redirect_to',
        { 'url': '/ticker/?filters=photo' },
        name='coltrane_photo_list'),
    url(r'^shouts/$', 'redirect_to',
        { 'url': '/ticker/?filters=shout' },
        name='coltrane_shout_root'),
    url(r'^shouts/page/(?P<page>[0-9]+)/$', 'redirect_to',
        { 'url': '/ticker/?filters=shout' },
        name='coltrane_link_list'),
    url(r'^tracks/$', 'redirect_to',
        { 'url': '/ticker/?filters=track' },
        name='coltrane_track_root'),
    url(r'^tracks/page/(?P<page>[0-9]+)/$', 'redirect_to',
        { 'url': '/ticker/?filters=track' },
        name='coltrane_track_list'),
    url(r'^categories/list/$', 'redirect_to', 
        { 'url': '/ticker/' },
        name='coltrane_category_list'),
    url(r'^apps/page/(?P<page>[0-9]+)/$', 'redirect_to',
        { 'url': '/apps/' },
        name='coltrane_app_root'),
    url(r'^posts/page/(?P<page>[0-9]+)/$', 'redirect_to',
        { 'url': '/posts/'}, name='coltrane_post_archive_index'),
    url(r'^ticker/page/(?P<page>[0-9]+)/$', 'redirect_to',
        { 'url': '/ticker/' },
        name='coltrane_ticker_root'),
)

# URLs for the new blog
urlpatterns += patterns('',
    
    # The index
    url(r'^$', 'coltrane.views.index', name='coltrane_index'),
    # Hard-coded flatpages
    url(r'^who-is-ben-welsh/$', direct_to_template,
        {'template': 'coltrane/bio.html'}, name="coltrane_bio"),
    url(r'^colophon/$', direct_to_template,
        {'template': 'coltrane/colophon.html'},
        name="coltrane_colophon"),
    # The admin
    (r'^admin/', include(admin.site.urls)),
    # Main list pages
    url(r'^apps/$', direct_to_template, {
            'template': 'coltrane/app_list.html',
            'extra_context': {
                'app_list': bona_fides.APP_LIST,
            }
        }, name='coltrane_app_list'),
    url(r'^clips/$', direct_to_template, {
            'template': 'coltrane/clip_list.html',
            'extra_context': {
                'clip_list': bona_fides.CLIP_LIST,
            }
        }, name='coltrane_clip_list'),
    url(r'^talks/$', direct_to_template,
        { 'template': 'coltrane/talk_list.html' },
        name='coltrane_talk_list'),
    url(r'^posts/$', 'django.views.generic.list_detail.object_list',
        {'queryset': Post.live.all().order_by("-pub_date")},
        name='coltrane_post_list'),
    url(r'^ticker/$', 'coltrane.views.ticker_detail',
        name='coltrane_ticker_list'),
    url(r'^ticker/page/(?P<page>[0-9]+).json$', 'coltrane.views.ticker_detail',
        {'response_type': 'json'},
        name='coltrane_ticker_json'),
    # Detail pages
    url(r'^posts/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$', 
        'coltrane.views.post_detail', name='coltrane_post_detail'),
    url(r'categories/(?P<slug>[-\w]+)/$', 'coltrane.views.category_detail',
        name="coltrane_category_detail"),
    url(r'^tags/(?P<tag>[^/]+)/$', 'coltrane.views.tag_detail',
        name='coltrane_tag_detail'),
    url(r'^corrections/(?P<id>[0-9]+)/$', 'coltrane.views.correx_redirect',
        name='coltrane_correx_redirect'),
    # Feeds
    url(r'^feeds/list/$', direct_to_template,
        {'template': 'coltrane/feed_list.html'}),
    
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
    url(r'feeds/tag/(?P<slug>[-\w]+)/$', feeds.TagFeed(), name="feeds-tag"),
    url(r'feeds/category/(?P<slug>[-\w]+)/$', feeds.CategoryFeed(), name="feeds-category"),
    url(r'feeds/corrections/$', feeds.RecentCorrections(), name="feeds-corrections"),
    url(r'feeds/movies/$', feeds.RecentMovies(), name="feeds-movies"),
    url(r'feeds/locations/$', feeds.RecentLocations(), name="feeds-locations"),
    url(r'feeds/questionheds/$', feeds.RecentHeds(), name="feeds-questionheds"),
    
    # Sitemaps
    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.index',
        {'sitemaps': sitemaps}),
    url(r'^sitemap-(?P<section>.+)\.xml$', 'django.contrib.sitemaps.views.sitemap',
        {'sitemaps': sitemaps}),
    # Robots and favicon
    url(r'^robots\.txt$', direct_to_template,
        {'template': 'robots.txt', 'mimetype': 'text/plain'}, name='robots'),
    url(r'^favicon.ico$', redirect_to, 
        {'url': 'http://palewire.s3.amazonaws.com/favicon.ico'}),
    # URL shortener
    (r'!/', include('shortener.urls')),
    # Kennedy name generator
    (r'^kennedy/', include('wxwtf.kennedy.urls')),
    # Flu Shots 2011
    url(r'free-flu-shots/$', 'wxwtf.flushots.views.index', name='flushots-index'),
    # Random Oscars Ballot
    url(r'random-oscars-ballot/$', 'wxwtf.random_oscars_ballot.views.index',
        name='random-oscars-ballot-index'),
    # newtwitter style autopagination with django
    url(r'^apps/twitter-style-infinite-scroll-with-django-demo/$',
        'coltrane.views.newtwitter_pagination_index',
        name='coltrane_app_newtwitter_index'),
    url(r'^apps/twitter-style-infinite-scroll-with-django-demo/json/(?P<page>[0-9]+)/',
        'coltrane.views.newtwitter_pagination_json',
        name='coltrane_app_newtwitter_json'),
    # BRING THE NEWS BACK
    url(r'^apps/bring-the-news-back/$', direct_to_template,
        {'template': 'wxwtf/bring_the_news_back/index.html' },
        name='coltrane_app_newtwitter_json'),
    # Return of the Mack ringtone
    url(r'^mack/$', direct_to_template, {'template': 'wxwtf/mack.html'},
        name='mack'),
    # Candy says...
    url(r'^candysays/$', direct_to_template, {'template': 'wxwtf/candy.html'},
        name='candy-says'),
    # Where will the Regional Connector go?
    url(r'^regional-connector/$', direct_to_template,
        {'template': 'wxwtf/regional_connector/index.html'},
        name='candy-says'),
    # Other weird stuff
    (r'^comments/', include('django.contrib.comments.urls')),
    (r'^correx/', include('correx.urls')),
    (r'^nicar/polls/', include("nicar.polls.urls")),
    (r'^nicar/flu-map/', include("nicar.flu_map.urls")),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.STATIC_ROOT, 'show_indexes': True, }),
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.STATIC_ROOT,
            'show_indexes': True,
        }),
        (r'^500/$', 'coltrane.views.server_error'),
    )
else:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.generic.simple.redirect_to',
             {'url': 'http://palewire.s3.amazonaws.com/%(path)s'}),
        (r'^static/(?P<path>.*)$', 'django.views.generic.simple.redirect_to',
             {'url': 'http://palewire.s3.amazonaws.com/%(path)s'}),
)

if settings.PRODUCTION:
    urlpatterns += patterns('',
        url(r'^munin/(?P<path>.*)$', staff_member_required(static_serve), {
            'document_root': settings.MUNIN_ROOT,
        })
   )


# 500 page fix
handler500 = 'coltrane.views.server_error'

