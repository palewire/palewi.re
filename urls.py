import os
this_dir = os.path.dirname(__file__)

from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

#import haystack
#haystack.autodiscover()

from coltrane.sitemaps import sitemaps

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
    (r'^scrape/albums/2006.html$', 'direct_to_template', {'template': 'flatpages/scrape/2006.html'}),
    (r'^scrape/albums/2007.html$', 'direct_to_template', {'template': 'flatpages/scrape/2007.html'}),
    # OpenLayers tutorial on old site.
    ('^openlayers-proportional-symbols/$', 'direct_to_template', {'template': 'flatpages/openlayers-proportional-symbols/index.html'}),
    # DC Music Stores map from old site.
    (r'^music/$', 'direct_to_template', {'template': 'flatpages/music/default.htm'}),
    # Arcade Fire hypecloud from old site.
    (r'^hypecloud/$', 'direct_to_template', {'template': 'flatpages/hypecloud/index.html'}),
    # DC Happy hours from old site.
    (r'^happyhours/$', 'direct_to_template', {'template': 'flatpages/happyhours/index.htm'}),
    (r'^happyhours/tuesday.htm$', 'direct_to_template', {'template': 'flatpages/happyhours/tuesday.htm'}),
    (r'^happyhours/wednesday.htm$', 'direct_to_template', {'template': 'flatpages/happyhours/wednesday.htm'}),
    (r'^happyhours/thursday.htm$', 'direct_to_template', {'template': 'flatpages/happyhours/thursday.htm'}),
    (r'^happyhours/friday.htm$', 'direct_to_template', {'template': 'flatpages/happyhours/friday.htm'}),
    (r'^happyhours/saturday.htm$', 'direct_to_template', {'template': 'flatpages/happyhours/saturday.htm'}),
    # Redirect old images from legacy site
    (r'^images/(?P<file_name>[^/]+)$', 'redirect_to', {'url': '/media/img/%(file_name)s'}),
    # Hard-coded flatpages
    (r'^who-is-ben-welsh/$', 'direct_to_template', {'template': 'flatpages/bio.html'}),
)

# URLs for the new blog
urlpatterns += patterns('',
    
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/(.*)', admin.site.root),
    
    (r'^applications/', include('coltrane.urls.apps')),
    (r'^books/', include('coltrane.urls.books')),
    (r'^commits/', include('coltrane.urls.commits')),
    (r'^categories/', include('coltrane.urls.categories')),
    (r'^corrections/', include('coltrane.urls.corrections')),
    (r'^links/', include('coltrane.urls.links')),
    (r'^locations/', include('coltrane.urls.locations')),
    (r'^movies/', include('coltrane.urls.movies')),
    (r'^photos/', include('coltrane.urls.photos')),
    (r'^posts/', include('coltrane.urls.posts')),
    (r'^shouts/', include('coltrane.urls.shouts')),
    (r'^tags/', include('coltrane.urls.tags')),
    (r'^tracks/', include('coltrane.urls.tracks')),
    
    (r'^comments/page/', include('coltrane.urls.comments')),
    (r'^comments/', include('django.contrib.comments.urls')),
    
    (r'^$', include('coltrane.urls.index')),
    (r'^ticker/', include('coltrane.urls.ticker')),
    
#    (r'^search/', include('haystack.urls')),
    (r'^feeds/', include('coltrane.urls.feeds')),
    (r'^sitemap.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
#    (r'^robots.txt$', include('robots.urls')),
    (r'^correx/', include('correx.urls')),
    (r'^cache/', include('django_memcached.urls')),

)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT }),
    )
else:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.generic.simple.redirect_to',
             {'url': 'http://palewire.s3.amazonaws.com/%(path)s'}),
    )


# Goofy pluggable apps
urlpatterns += patterns('',
    (r'^kennedy/', include('kennedy.urls')),
    #(r'^rapture/', include('rapture.urls')),
)
