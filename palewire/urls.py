import os
this_dir = os.path.dirname(__file__)

from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

	(r'^admin/doc/', include('django.contrib.admindocs.urls')),
	(r'^admin/(.*)', admin.site.root),
	(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT }),
	
	(r'^categories/', include('coltrane.urls.categories')),
	(r'^feeds/', include('coltrane.urls.feeds')),
	(r'^links/', include('coltrane.urls.links')),
	(r'^tags/', include('coltrane.urls.tags')),
	(r'^posts/', include('coltrane.urls.posts')),
	(r'^tweets/', include('coltrane.urls.tweets')),
	(r'^videos/', include('coltrane.urls.videos')),
	(r'^photos/', include('coltrane.urls.photos')),
	(r'^tracks/', include('coltrane.urls.tracks')),
	(r'^comments/page/', include('coltrane.urls.comments')),
	(r'^comments/', include('django.contrib.comments.urls')),
	(r'^$', include('coltrane.urls.tumblers')),
	(r'^tumblr/', include('coltrane.urls.tumblers')),
)

