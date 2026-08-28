from django.conf import settings
from django.contrib.sitemaps import views as sitemap_views
from django.urls import path, re_path
from django.views.generic import RedirectView, TemplateView

# Views
from coltrane import views
from coltrane.feeds import LatestPostsFeed
from coltrane.sitemaps import sitemaps
from toolbox.views import health_check

urlpatterns = [
    # Health check
    path("health/", health_check, name="health_check"),
    # The index
    path("", RedirectView.as_view(url="/who-is-ben-welsh/"), name="coltrane_index"),
    # My bio
    path("who-is-ben-welsh/", views.bio, name="coltrane_bio"),
    # Main list pages
    path("posts/", views.PostListView.as_view(), name="coltrane_post_list"),
    path("clips/", views.ClipListView.as_view(), name="coltrane_clip_list"),
    path("apps/", views.AppListView.as_view(), name="coltrane_app_list"),
    path("code/", views.CodeListView.as_view(), name="coltrane_code_list"),
    path("guides/", views.GuideListView.as_view(), name="coltrane_guide_list"),
    path("talks/", views.TalkListView.as_view(), name="coltrane_talk_list"),
    path("bots/", views.BotListView.as_view(), name="coltrane_bot_list"),
    # Replaced list pages
    path("work/", RedirectView.as_view(pattern_name="coltrane_clip_list")),
    path("docs/", TemplateView.as_view(template_name="coltrane/docs_landing.html"), name="coltrane_docs_landing"),
    # Detail pages
    re_path(
        r"^posts/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$",
        views.post_detail,
        name="coltrane_post_detail",
    ),
    # Sitemaps
    path("sitemap.xml", sitemap_views.index, {"sitemaps": sitemaps}),
    path(
        "sitemap-<str:section>.xml",
        sitemap_views.sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    # Plain-text site metadata
    path("feeds/posts/", LatestPostsFeed()),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots",
    ),
    path(
        ".well-known/security.txt",
        TemplateView.as_view(template_name="security.txt", content_type="text/plain; charset=utf-8"),
        name="security_txt",
    ),
    path("favicon.ico", RedirectView.as_view(url=f"{settings.STATIC_URL}favicon.ico"), name="favicon"),
    path("@palewire", views.username_redirect),
]
