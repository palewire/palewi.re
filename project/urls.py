from django.conf import settings
from django.conf.urls import include, url
from .redirects import patterns as redirectpatterns

# Views
from coltrane import views
from coltrane.sitemaps import sitemaps
from toolbox import views as toolbox_views
from toolbox.views import DirectTemplateView
from django.views.generic import RedirectView
from django.views.static import serve as static_serve
from django.contrib.sitemaps import views as sitemap_views

# Admin
from django.contrib import admin
from django.urls import path


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
    path('admin/', admin.site.urls),

    # Main list pages
    url(r'^work/$', views.ClipListView.as_view(), name='coltrane_work_list'),
    url(r'^talks/$', views.TalkListView.as_view(), name='coltrane_talk_list'),
    url(r'^posts/$', views.PostListView.as_view(), name='coltrane_post_list'),

    # Detail pages
    url(
        r'^posts/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$',
        views.post_detail,
        name='coltrane_post_detail'
    ),

    # Sitemaps
    url(
        r'^sitemap\.xml$',
        sitemap_views.index,
        {'sitemaps': sitemaps}
    ),
    url(
        r'^sitemap-(?P<section>.+)\.xml$',
        sitemap_views.sitemap,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap'
    ),

    # Robots and favicon
    url(
        r'^robots\.txt$',
        DirectTemplateView.as_view(
            template_name='robots.txt',
            content_type='text/plain'
        ),
        name='robots'
    ),
    url(
        r'^favicon.ico$',
        RedirectView.as_view(
            url='http://palewire.s3.amazonaws.com/favicon.ico'
        )
    ),

    # Corrections
    url(r'^comments/', include('django_comments.urls')),

    # Static and media
    url(r'^media/(?P<path>.*)$', RedirectView.as_view(
         url='http://palewire.s3.amazonaws.com/%(path)s')),
    url(r'^static/(?P<path>.*)$', RedirectView.as_view(
         url='http://palewire.s3.amazonaws.com/%(path)s')),
]

# Combine patterns
urlpatterns = redirectpatterns
urlpatterns += blogpatterns

# 500 page fix
handler500 = 'coltrane.views.server_error'
