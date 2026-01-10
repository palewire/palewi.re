from django.urls import re_path
from django.views.generic import RedirectView
from toolbox.views import DirectTemplateView


patterns = [
    # Redirect links to old blog to new posts
    re_path(
        r"^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$",
        RedirectView.as_view(url="/posts/%(year)s/%(month)s/%(day)s/%(slug)s/"),
    ),
    # Redirects old tag pages
    re_path(r"^tag/(?P<tag>[^/]+)/$", RedirectView.as_view(url="/who-is-ben-welsh/")),
    re_path(r"^tags/(?P<tag>[^/]+)/$", RedirectView.as_view(url="/who-is-ben-welsh/")),
    # Redirects old feeds
    re_path(r"^comments/feed/$", RedirectView.as_view(url="/")),
    re_path(r"^feed/$", RedirectView.as_view(url="/")),
    re_path(r"^feed/atom/$", RedirectView.as_view(url="/")),
    re_path(r"^feed/rss/$", RedirectView.as_view(url="/")),
    # Redirects from old flatpages
    re_path(r"^bio/$", RedirectView.as_view(url="/who-is-ben-welsh/")),
    # Redirects from old clips pages
    re_path(r"^apps/$", RedirectView.as_view(url="/work/"), name="coltrane_app_list"),
    re_path(r"^clips/$", RedirectView.as_view(url="/work/"), name="coltrane_clip_list"),
    # Scrape pages from tutorial on old site.
    re_path(
        r"^scrape/albums/2006.html$",
        DirectTemplateView.as_view(template_name="tutorials/scrape/2006.html"),
    ),
    re_path(
        r"^scrape/albums/2007.html$",
        DirectTemplateView.as_view(template_name="tutorials/scrape/2007.html"),
    ),
    # OpenLayers tutorial on old site.
    re_path(
        "^openlayers-proportional-symbols/$",
        DirectTemplateView.as_view(
            template_name="tutorials/openlayers-proportional-symbols/index.html"
        ),
    ),
    # 2011 free flu shots app
    re_path(
        r"^free-flu-shots/$",
        RedirectView.as_view(
            url="https://web.archive.org/web/20130718063144/palewi.re/free-flu-shots/"
        ),
    ),
    re_path(
        r"^random-oscars-ballot/$",
        RedirectView.as_view(
            url="https://web.archive.org/web/20191110225501/https://palewi.re/random-oscars-ballot/"
        ),
    ),
    re_path(
        r"^kennedy/$",
        RedirectView.as_view(
            url="https://web.archive.org/web/20160413124128/http://palewi.re/kennedy/"
        ),
    ),
    re_path(
        r"^colophon/$",
        RedirectView.as_view(
            url="https://web.archive.org/web/20191110230741/https://palewi.re/colophon/"
        ),
    ),
    re_path(
        r"^apps/twitter-style-infinite-scroll-with-django-demo/$",
        RedirectView.as_view(
            url="https://web.archive.org/web/20161227151249/http://palewi.re/apps/twitter-style-infinite-scroll-with-django-demo/"
        ),
    ),
    re_path(
        r"^apps/bring-the-news-back/$",
        RedirectView.as_view(
            url="https://web.archive.org/web/20191110231324/http://palewi.re/apps/bring-the-news-back/"
        ),
    ),
    re_path(
        r"^mack/$",
        RedirectView.as_view(
            url="https://web.archive.org/web/20121109101143/http://palewi.re/mack/"
        ),
    ),
    re_path(
        r"^mack/$",
        RedirectView.as_view(
            url="https://web.archive.org/web/20160413123742/http://palewi.re/candysays/"
        ),
    ),
    re_path(
        r"^regional-connector/$",
        RedirectView.as_view(
            url="https://web.archive.org/web/20161229055224/http://palewi.re/regional-connector/"
        ),
    ),
    re_path(
        r"^nicar/polls/$",
        RedirectView.as_view(
            url="https://web.archive.org/web/20191110232017/https://palewi.re/nicar/polls/"
        ),
    ),
    re_path(
        r"^nicar/flu-map/$",
        RedirectView.as_view(
            url="https://web.archive.org/web/20191110232108/https://palewi.re/nicar/flu-map/"
        ),
    ),
    # DC Music Stores map from old site.
    re_path(r"^music/$", RedirectView.as_view(url="/")),
    # Arcade Fire hypecloud from old site.
    re_path(r"^hypecloud/$", RedirectView.as_view(url="/")),
    # DC Happy hours from old site.
    re_path(r"^happyhours/$", RedirectView.as_view(url="/")),
    re_path(r"^happyhours/(?P<whatever>.*)", RedirectView.as_view(url="/")),
    # Redirect old images from legacy site
    re_path(
        r"^images/(?P<file_name>[^/]+)$",
        RedirectView.as_view(url="/media/img/%(file_name)s"),
    ),
    # Longer apps urls
    re_path(r"^applications/$", RedirectView.as_view(url="/apps/")),
    re_path(
        r"^applications/(?P<anything>.*)/$",
        RedirectView.as_view(url="/apps/%(anything)s/"),
    ),
    # V2 of the blog, now replaced by the consolidated ticker
    re_path(
        r"^books/$",
        RedirectView.as_view(url="/ticker/?filters=book"),
        name="coltrane_book_root",
    ),
    re_path(
        r"^books/page/(?P<page>[0-9]+)/$",
        RedirectView.as_view(url="/ticker/?filters=book"),
        name="coltrane_book_list",
    ),
    re_path(
        r"^comments/$",
        RedirectView.as_view(url="/ticker/?filters=comment"),
        name="coltrane_comment_root",
    ),
    re_path(
        r"^comments/page/(?P<page>[0-9]+)/$",
        RedirectView.as_view(url="/ticker/?filters=comment"),
        name="coltrane_comment_list",
    ),
    re_path(
        r"^commits/$",
        RedirectView.as_view(url="/ticker/?filters=commit"),
        name="coltrane_commit_root",
    ),
    re_path(
        r"^commits/page/(?P<page>[0-9]+)/$",
        RedirectView.as_view(url="/ticker/?filters=commit"),
        name="coltrane_commit_list",
    ),
    re_path(
        r"^links/$",
        RedirectView.as_view(url="/ticker/?filters=link"),
        name="coltrane_link_root",
    ),
    re_path(
        r"^links/page/(?P<page>[0-9]+)/$",
        RedirectView.as_view(url="/ticker/?filters=link"),
        name="coltrane_link_list",
    ),
    re_path(
        r"^locations/$",
        RedirectView.as_view(url="/ticker/?filters=location"),
        name="coltrane_location_root",
    ),
    re_path(
        r"^locations/page/(?P<page>[0-9]+)/$",
        RedirectView.as_view(url="/ticker/?filters=location"),
        name="coltrane_location_list",
    ),
    re_path(
        r"^movies/$",
        RedirectView.as_view(url="/ticker/?filters=movie"),
        name="coltrane_movie_root",
    ),
    re_path(
        r"^movies/page/(?P<page>[0-9]+)/$",
        RedirectView.as_view(url="/ticker/?filters=movie"),
        name="coltrane_movie_list",
    ),
    re_path(
        r"^photos/$",
        RedirectView.as_view(url="/ticker/?filters=photo"),
        name="coltrane_photo_root",
    ),
    re_path(
        r"^photos/page/(?P<page>[0-9]+)/$",
        RedirectView.as_view(url="/ticker/?filters=photo"),
        name="coltrane_photo_list",
    ),
    re_path(
        r"^shouts/$",
        RedirectView.as_view(url="/ticker/?filters=shout"),
        name="coltrane_shout_root",
    ),
    re_path(
        r"^shouts/page/(?P<page>[0-9]+)/$",
        RedirectView.as_view(url="/ticker/?filters=shout"),
        name="coltrane_link_list",
    ),
    re_path(
        r"^tracks/$",
        RedirectView.as_view(url="/ticker/?filters=track"),
        name="coltrane_track_root",
    ),
    re_path(
        r"^tracks/page/(?P<page>[0-9]+)/$",
        RedirectView.as_view(url="/ticker/?filters=track"),
        name="coltrane_track_list",
    ),
    re_path(
        r"^categories/list/$",
        RedirectView.as_view(url="/ticker/"),
        name="coltrane_category_list",
    ),
    re_path(
        r"^apps/page/(?P<page>[0-9]+)/$",
        RedirectView.as_view(url="/apps/"),
        name="coltrane_app_root",
    ),
    re_path(
        r"^posts/page/(?P<page>[0-9]+)/$",
        RedirectView.as_view(url="/posts/"),
        name="coltrane_post_archive_index",
    ),
    re_path(
        r"^ticker/page/(?P<page>[0-9]+)/$",
        RedirectView.as_view(url="/ticker/"),
        name="coltrane_ticker_root",
    ),
]
