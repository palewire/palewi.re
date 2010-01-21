# URLs
from django.conf.urls.defaults import *


urlpatterns = patterns('correx.views',

	url(r'^admin/filter/contenttype/$', 'filter_contenttypes_by_app', name="filter-contenttypes-by-app"),

)