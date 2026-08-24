from django.urls import path, re_path
from django.views.generic import RedirectView

STATIC_REDIRECTS = {
    "comments/feed/": "/",
    "feed/": "/",
    "feed/atom/": "/",
    "feed/rss/": "/",
    "bio/": "/who-is-ben-welsh/",
    "apps/": "/work/",
    "clips/": "/work/",
    "free-flu-shots/": "https://web.archive.org/web/20130718063144/palewi.re/free-flu-shots/",
    "random-oscars-ballot/": "https://web.archive.org/web/20191110225501/https://palewi.re/random-oscars-ballot/",
    "kennedy/": "https://web.archive.org/web/20160413124128/http://palewi.re/kennedy/",
    "colophon/": "https://web.archive.org/web/20191110230741/https://palewi.re/colophon/",
    "apps/twitter-style-infinite-scroll-with-django-demo/": (
        "https://web.archive.org/web/20161227151249/http://palewi.re/apps/twitter-style-infinite-scroll-with-django-demo/"
    ),
    "apps/bring-the-news-back/": "https://web.archive.org/web/20191110231324/http://palewi.re/apps/bring-the-news-back/",
    "mack/": "https://web.archive.org/web/20121109101143/http://palewi.re/mack/",
    "candysays/": "https://web.archive.org/web/20160413123742/http://palewi.re/candysays/",
    "regional-connector/": "https://web.archive.org/web/20161229055224/http://palewi.re/regional-connector/",
    "nicar/polls/": "https://web.archive.org/web/20191110232017/https://palewi.re/nicar/polls/",
    "nicar/flu-map/": "https://web.archive.org/web/20191110232108/https://palewi.re/nicar/flu-map/",
    "music/": "/",
    "hypecloud/": "/",
    "happyhours/": "/",
    "applications/": "/apps/",
}

patterns = [
    *(path(source, RedirectView.as_view(url=destination)) for source, destination in STATIC_REDIRECTS.items()),
    # Redirect links to old blog to new posts
    re_path(
        r"^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$",
        RedirectView.as_view(url="/posts/%(year)s/%(month)s/%(day)s/%(slug)s/"),
    ),
    # Redirects old tag pages
    path("tag/<str:tag>/", RedirectView.as_view(url="/who-is-ben-welsh/")),
    path("tags/<str:tag>/", RedirectView.as_view(url="/who-is-ben-welsh/")),
    path("happyhours/<path:whatever>", RedirectView.as_view(url="/")),
    # Redirect old images from legacy site
    path(
        "images/<str:file_name>",
        RedirectView.as_view(url="https://palewire.s3.amazonaws.com/img/%(file_name)s"),
    ),
    # Longer apps urls
    path(
        "applications/<path:anything>/",
        RedirectView.as_view(url="/apps/%(anything)s/"),
    ),
    path(
        "apps/page/<int:page>/",
        RedirectView.as_view(url="/apps/"),
    ),
    path(
        "posts/page/<int:page>/",
        RedirectView.as_view(url="/posts/"),
    ),
]
