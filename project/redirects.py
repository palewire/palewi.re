from django.conf.urls import url
from django.views.generic import RedirectView
from toolbox.views import DirectTemplateView


patterns = [
    # Redirect links to old blog to new posts
    url(r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$',
        RedirectView.as_view(url='/posts/%(year)s/%(month)s/%(day)s/%(slug)s/')
    ),
    # Redirects old tag pages
    url(r'^tag/(?P<tag>[^/]+)/$', RedirectView.as_view(url='/who-is-ben-welsh/')),
    url(r'^tags/(?P<tag>[^/]+)/$', RedirectView.as_view(url='/who-is-ben-welsh/')),
    # Redirects old feeds to new feeds
    url(r'^comments/feed/$', RedirectView.as_view(url='/feeds/comments/')),
    url(r'^feed/$', RedirectView.as_view(url='/feeds/posts/')),
    url(r'^feed/atom/$', RedirectView.as_view(url='/feeds/posts/')),
    url(r'^feed/rss/$', RedirectView.as_view(url='/feeds/posts/')),
    # Redirects from old flatpages
    url(r'^bio/$', RedirectView.as_view(url='/who-is-ben-welsh/')),
    # Redirects from old clips pages
    url(r'^apps/$', RedirectView.as_view(url='/work/'), name='coltrane_app_list'),
    url(r'^clips/$', RedirectView.as_view(url='/work/'), name='coltrane_clip_list'),
    # Scrape pages from tutorial on old site.
    url(r'^scrape/albums/2006.html$', DirectTemplateView.as_view(
        template_name='tutorials/scrape/2006.html')),
    url(r'^scrape/albums/2007.html$', DirectTemplateView.as_view(
        template_name='tutorials/scrape/2007.html')),
    # OpenLayers tutorial on old site.
    url('^openlayers-proportional-symbols/$', DirectTemplateView.as_view(
        template_name='tutorials/openlayers-proportional-symbols/index.html')),
    # 2011 free flu shots app
    url(
        r'^free-flu-shots/$',
        RedirectView.as_view(
            url='https://web.archive.org/web/20130718063144/palewi.re/free-flu-shots/'
        )
    ),
    url(
        r'^random-oscars-ballot/$',
        RedirectView.as_view(
            url='https://web.archive.org/web/20191110225501/https://palewi.re/random-oscars-ballot/'
        )
    ),
    # DC Music Stores map from old site.
    url(r'^music/$', RedirectView.as_view(url='/')),
    # Arcade Fire hypecloud from old site.
    url(r'^hypecloud/$', RedirectView.as_view(url='/')),
    # DC Happy hours from old site.
    url(r'^happyhours/$', RedirectView.as_view(url='/')),
    url(r'^happyhours/(?P<whatever>.*)', RedirectView.as_view(url='/')),
    # Redirect old images from legacy site
    url(r'^images/(?P<file_name>[^/]+)$', RedirectView.as_view(
        url='/media/img/%(file_name)s')),
    # Longer apps urls
    url(r'^applications/$', RedirectView.as_view(url='/apps/')),
    url(r'^applications/(?P<anything>.*)/$', RedirectView.as_view(
        url='/apps/%(anything)s/')),
    # V2 of the blog, now replaced by the consolidated ticker
    url(r'^books/$', RedirectView.as_view(url='/ticker/?filters=book'),
        name='coltrane_book_root'),
    url(r'^books/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=book'), name='coltrane_book_list'),
    url(r'^comments/$', RedirectView.as_view(url='/ticker/?filters=comment'),
        name='coltrane_comment_root'),
    url(r'^comments/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=comment'), name='coltrane_comment_list'),
    url(r'^commits/$', RedirectView.as_view(url='/ticker/?filters=commit'),
        name='coltrane_commit_root'),
    url(r'^commits/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=commit'), name='coltrane_commit_list'),
    url(r'^corrections/$', RedirectView.as_view(url='/ticker/?filters=change'),
        name='coltrane_correx_root'),
    url(r'^corrections/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=change'), name='coltrane_correx_list'),
    url(r'^links/$', RedirectView.as_view(url='/ticker/?filters=link'),
        name='coltrane_link_root'),
    url(r'^links/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=link'), name='coltrane_link_list'),
    url(r'^locations/$', RedirectView.as_view(url='/ticker/?filters=location'),
        name='coltrane_location_root'),
    url(r'^locations/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=location'), name='coltrane_location_list'),
    url(r'^movies/$', RedirectView.as_view(url='/ticker/?filters=movie'),
        name='coltrane_movie_root'),
    url(r'^movies/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=movie'), name='coltrane_movie_list'),
    url(r'^photos/$', RedirectView.as_view(url='/ticker/?filters=photo'),
        name='coltrane_photo_root'),
    url(r'^photos/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=photo'), name='coltrane_photo_list'),
    url(r'^shouts/$', RedirectView.as_view(url='/ticker/?filters=shout'),
        name='coltrane_shout_root'),
    url(r'^shouts/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=shout'), name='coltrane_link_list'),
    url(r'^tracks/$', RedirectView.as_view(url='/ticker/?filters=track'),
        name='coltrane_track_root'),
    url(r'^tracks/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/?filters=track'), name='coltrane_track_list'),
    url(r'^categories/list/$', RedirectView.as_view(url='/ticker/'),
        name='coltrane_category_list'),
    url(r'^apps/page/(?P<page>[0-9]+)/$', RedirectView.as_view(url='/apps/'),
        name='coltrane_app_root'),
    url(r'^posts/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/posts/'), name='coltrane_post_archive_index'),
    url(r'^ticker/page/(?P<page>[0-9]+)/$', RedirectView.as_view(
        url='/ticker/'), name='coltrane_ticker_root'),
]
