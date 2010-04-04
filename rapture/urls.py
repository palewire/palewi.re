from django.conf.urls.defaults import *

from django.conf import settings

urlpatterns = patterns('',

    url(r'^$', 'rapture.archive.views.index', name="rapture-index"),
    
    # Data downloads
    url(r'^download/csv/$', 'rapture.data.views.csv', name="rapture-download-csv"),
    url(r'^download/json/$', 'rapture.data.views.json', name="rapture-download-json"),
    url(r'^download/xml/$', 'rapture.data.views.xml', name="rapture-download-xml"),
    url(r'^download/xls/$', 'rapture.data.views.xls', name="rapture-download-xls"),
    
    # Archives
    url(r'^archive/snapshot/list/$', 'rapture.archive.views.archive_list', name="rapture-archive-list"),
    url(r'^archive/snapshot/(?P<id>[0-9]+)/$', 'rapture.archive.views.archive_detail', name="rapture-archive-detail"),
    url(r'^archive/snapshot/media/(?P<path>.*)$', 'rapture.archive.views.archive_media', name="rapture-archive-media"),

)









