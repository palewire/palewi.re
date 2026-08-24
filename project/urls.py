# Admin
from django.contrib import admin
from django.contrib.sitemaps import views as sitemap_views
from django.urls import path, re_path
from django.views.generic import RedirectView

# Views
from coltrane import views
from coltrane.feeds import LatestPostsFeed
from coltrane.sitemaps import sitemaps
from toolbox.views import DirectTemplateView, health_check

from .redirects import patterns as redirectpatterns

# URLs for the blog
blogpatterns = [
    # Health check
    path("health/", health_check, name="health_check"),
    # The index
    re_path(r"^$", RedirectView.as_view(url="/who-is-ben-welsh/"), name="coltrane_index"),
    # My bio
    re_path(r"^who-is-ben-welsh/$", views.bio, name="coltrane_bio"),
    # The admin
    path("admin/", admin.site.urls),
    # Main list pages
    re_path(r"^work/$", views.ClipListView.as_view(), name="coltrane_work_list"),
    re_path(r"^talks/$", views.TalkListView.as_view(), name="coltrane_talk_list"),
    re_path(r"^posts/$", views.PostListView.as_view(), name="coltrane_post_list"),
    re_path(r"^docs/$", views.DocListView.as_view(), name="coltrane_doc_list"),
    re_path(r"^bots/$", views.BotListView.as_view(), name="coltrane_bot_list"),
    # Detail pages
    re_path(
        r"^posts/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$",
        views.post_detail,
        name="coltrane_post_detail",
    ),
    # Sitemaps
    re_path(r"^sitemap\.xml$", sitemap_views.index, {"sitemaps": sitemaps}),
    re_path(
        r"^sitemap-(?P<section>.+)\.xml$",
        sitemap_views.sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    # Robots and favicon
    path("feeds/posts/", LatestPostsFeed()),
    re_path(
        r"^robots\.txt$",
        DirectTemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots",
    ),
    re_path(r"^favicon\.ico$", RedirectView.as_view(url="/static/favicon.ico"), name="favicon"),
    # Mastodon
    path(".well-known/webfinger", views.wellknown_webfinger),
    path(".well-known/host-meta", views.wellknown_hostmeta),
    path(".well-known/nodeinfo", views.wellknown_nodeinfo),
    path("@palewire", views.username_redirect),
]

# Combine patterns
urlpatterns = redirectpatterns
urlpatterns += blogpatterns

# 500 page fix
handler500 = "coltrane.views.server_error"
