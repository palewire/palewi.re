import os
this_dir = os.path.dirname(__file__)

from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

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

)

# URLs for the new blog
urlpatterns += patterns('',

	(r'^admin/doc/', include('django.contrib.admindocs.urls')),
	(r'^admin/(.*)', admin.site.root),
	(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT }),
	
	(r'^categories/', include('coltrane.urls.categories')),
	(r'^links/', include('coltrane.urls.links')),
	(r'^tags/', include('coltrane.urls.tags')),
	(r'^posts/', include('coltrane.urls.posts')),
	(r'^shouts/', include('coltrane.urls.shouts')),
	(r'^photos/', include('coltrane.urls.photos')),
	(r'^tracks/', include('coltrane.urls.tracks')),

	(r'^comments/page/', include('coltrane.urls.comments')),
	(r'^comments/', include('django.contrib.comments.urls')),

	(r'^$', include('coltrane.urls.ticker')),
	(r'^ticker/', include('coltrane.urls.ticker')),

	(r'^search/', include('solango.urls')),
	(r'^feeds/', include('coltrane.urls.feeds')),
	(r'^sitemap.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
	(r'^robots.txt$', include('robots.urls')),
)
