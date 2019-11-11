import os
this_dir = os.path.dirname(__file__)

from django.conf.urls import include, url
from django.conf import settings
from django.contrib import admin
import bona_fides
from coltrane import views
from coltrane.models import Post
from coltrane.sitemaps import sitemaps
from bona_fides.models import Clip, Talk
from redirects import patterns as redirectpatterns
from django.contrib.sitemaps import views as sitemap_views
from django.views.static import serve as static_serve
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import RedirectView, ListView
from toolbox.views import DirectTemplateView
from toolbox import views as toolbox_views
admin.autodiscover()


# URLs for the blog
blogpatterns = [

    # The index
    url(
        r'^$',
        RedirectView.as_view(url='/who-is-ben-welsh/'),
        name='coltrane_index'
    ),
    # My bio
    url(r'^who-is-ben-welsh/$', views.bio, name="coltrane_bio"),
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

    # Detail pages
    url(r'^posts/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$',
        views.post_detail, name='coltrane_post_detail'),
    url(r'categories/(?P<slug>[-\w]+)/$', views.category_detail,
        name="coltrane_category_detail"),

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

    # Corrections
    url(r'^comments/', include('django_comments.urls')),
    url(r'^correx/', include('correx.urls')),
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
