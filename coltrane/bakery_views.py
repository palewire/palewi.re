from collections.abc import Callable
from os import PathLike

from bakery.views.base import Buildable404View, Buildable500View, BuildableMixin, BuildableTemplateView
from bakery.views.list import BuildableListView
from django.conf import settings
from django.contrib.sitemaps import views as sitemap_views
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.test import RequestFactory
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView

from coltrane.content_loaders import MarkdownPost, load_awards, load_bots, load_clips, load_docs, load_posts, load_talks
from coltrane.feeds import LatestPostsFeed
from coltrane.sitemaps import sitemaps
from coltrane.views import BIO_EMAIL_LIST, BIO_SKILL_LIST, BIO_SOCIAL_LIST, _load_bio_html


class CanonicalBuildMixin:
    """Build URLs using the public host so feeds and sitemaps remain canonical."""

    def create_request(self, path: str | PathLike[str]) -> HttpRequest:
        return RequestFactory().get(
            str(path),
            HTTP_HOST=settings.BAKERY_BUILD_HOST,
            secure=True,
            headers={"X-Bakery": "true"},
        )


class BioBuildView(CanonicalBuildMixin, BuildableTemplateView):
    build_path = "who-is-ben-welsh/index.html"
    template_name = "coltrane/bio.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "bio_html": mark_safe(_load_bio_html()),
                "award_list": load_awards(),
                "socialmedia_list": BIO_SOCIAL_LIST,
                "email_list": BIO_EMAIL_LIST,
                "skill_list": BIO_SKILL_LIST,
            }
        )
        return context


class ClipListBuildView(CanonicalBuildMixin, BuildableTemplateView):
    build_path = "work/index.html"
    template_name = "coltrane/clip_list.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context["object_list"] = load_clips()
        return context


class TalkListBuildView(CanonicalBuildMixin, BuildableTemplateView):
    build_path = "talks/index.html"
    template_name = "coltrane/talk_list.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context["object_list"] = load_talks()
        return context


class PostListBuildView(CanonicalBuildMixin, BuildableListView):
    build_path = "posts/index.html"
    template_name = "coltrane/post_list.html"

    def get_queryset(self) -> list[MarkdownPost]:
        return load_posts()


class DocListBuildView(CanonicalBuildMixin, BuildableTemplateView):
    build_path = "docs/index.html"
    template_name = "coltrane/doc_list.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        all_docs = load_docs()
        context["lesson_list"] = [doc for doc in all_docs if doc.type == "lesson-plan"]
        context["software_list"] = [doc for doc in all_docs if doc.type == "software"]
        return context


class BotListBuildView(CanonicalBuildMixin, BuildableTemplateView):
    build_path = "bots/index.html"
    template_name = "coltrane/bot_list.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context["object_list"] = load_bots()
        return context


class PostDetailBuildView(CanonicalBuildMixin, TemplateView, BuildableMixin):
    template_name = "coltrane/post_detail.html"

    @property
    def build_method(self) -> Callable[[], None]:
        return self.build

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context["object"] = self.post
        return context

    def build(self) -> None:
        for self.post in load_posts():
            build_path = f"{self.post.get_absolute_url().lstrip('/')}index.html"
            self.request = self.create_request(self.post.get_absolute_url())
            self.prep_directory(build_path)
            self.build_file(self.get_output_path(build_path), self.get_content())


class LatestPostsBuildFeed(CanonicalBuildMixin, LatestPostsFeed):
    build_path = "feeds/posts/index.xml"
    feed_url = "/feeds/posts/"


class RobotsBuildView(CanonicalBuildMixin, BuildableTemplateView):
    build_path = "robots.txt"
    content_type = "text/plain"
    template_name = "robots.txt"


class SecurityTxtBuildView(CanonicalBuildMixin, BuildableTemplateView):
    build_path = ".well-known/security.txt"
    content_type = "text/plain; charset=utf-8"
    template_name = "security.txt"


class Static404BuildView(CanonicalBuildMixin, Buildable404View):
    pass


class Static500BuildView(CanonicalBuildMixin, Buildable500View):
    pass


class BuildableSitemapView(CanonicalBuildMixin, BuildableMixin):
    build_path: str

    @property
    def build_method(self) -> Callable[[], None]:
        return self.build

    def build(self) -> None:
        self.request = self.create_request(f"/{self.build_path}")
        response = self.get_response().render()
        self.prep_directory(self.build_path)
        self.build_file(self.get_output_path(self.build_path), response.content)

    def get_response(self) -> TemplateResponse:
        raise NotImplementedError


class SitemapIndexBuildView(BuildableSitemapView):
    build_path = "sitemap.xml"

    def get_response(self):
        return sitemap_views.index(self.request, sitemaps=sitemaps)


class StaticSitemapBuildView(BuildableSitemapView):
    build_path = "sitemap-static.xml"

    def get_response(self):
        return sitemap_views.sitemap(self.request, sitemaps=sitemaps, section="static")


class PostsSitemapBuildView(BuildableSitemapView):
    build_path = "sitemap-posts.xml"

    def get_response(self):
        return sitemap_views.sitemap(self.request, sitemaps=sitemaps, section="posts")
