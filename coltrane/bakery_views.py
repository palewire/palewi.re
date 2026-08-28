from collections.abc import Callable, Sequence
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

from coltrane.content_loaders import (
    App,
    AppCategory,
    CodeCategory,
    CodeProject,
    Doc,
    MarkdownPost,
    group_apps,
    group_code,
    load_apps,
    load_awards,
    load_bots,
    load_clip_updates,
    load_clips,
    load_code,
    load_docs,
    load_posts,
    load_talks,
)
from coltrane.feeds import LatestPostsFeed, LatestPostsJsonFeed
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
    build_path = "clips/index.html"
    template_name = "coltrane/clip_list.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context["object_list"] = [clip for clip in load_clips() if clip.type in {"app", "story"}]
        return context


class CatalogListBuildView(CanonicalBuildMixin, BuildableTemplateView):
    template_name = "coltrane/catalog_list.html"
    page_description: str
    page_slug: str
    page_title: str
    catalog_heading: str
    update_type: str | None
    updates_heading = "Updates"

    def get_catalog(self) -> Sequence[App | CodeProject | Doc]:
        raise NotImplementedError

    def get_category_list(
        self,
        catalog: Sequence[App | CodeProject | Doc],
    ) -> Sequence[AppCategory | CodeCategory]:
        return []

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        catalog = self.get_catalog()
        context.update(
            {
                "catalog_heading": self.catalog_heading,
                "category_list": self.get_category_list(catalog),
                "object_list": catalog,
                "page_description": self.page_description,
                "page_slug": self.page_slug,
                "page_title": self.page_title,
                "update_list": load_clip_updates(self.update_type, catalog) if self.update_type else [],
                "updates_heading": self.updates_heading,
            }
        )
        return context


class AppListBuildView(CatalogListBuildView):
    build_path = "apps/index.html"
    catalog_heading = ""
    page_description = "My independent network of Internet publications"
    page_slug = "apps"
    page_title = "Apps"
    update_type = "service"

    def get_catalog(self) -> Sequence[App]:
        return load_apps()

    def get_category_list(
        self,
        catalog: Sequence[App | CodeProject | Doc],
    ) -> Sequence[AppCategory]:
        return group_apps([item for item in catalog if isinstance(item, App)])


class TalkListBuildView(CanonicalBuildMixin, BuildableTemplateView):
    build_path = "talks/index.html"
    template_name = "coltrane/talk_list.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context["object_list"] = load_talks()
        return context


class TalkDetailBuildView(CanonicalBuildMixin, TemplateView, BuildableMixin):
    template_name = "coltrane/talk_detail.html"

    @property
    def build_method(self) -> Callable[[], None]:
        return self.build

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context["object"] = self.talk
        return context

    def build(self) -> None:
        for self.talk in load_talks():
            if not self.talk.slug:
                continue
            build_path = f"{self.talk.get_absolute_url().lstrip('/')}index.html"
            self.request = self.create_request(self.talk.get_absolute_url())
            self.prep_directory(build_path)
            self.build_file(self.get_output_path(build_path), self.get_content())


class PostListBuildView(CanonicalBuildMixin, BuildableListView):
    build_path = "posts/index.html"
    template_name = "coltrane/post_list.html"

    def get_queryset(self) -> list[MarkdownPost]:
        return load_posts()


class DocListBuildView(CatalogListBuildView):
    doc_type: str
    update_type: str | None

    def get_catalog(self) -> Sequence[Doc]:
        return [doc for doc in load_docs() if doc.type == self.doc_type]


class CodeListBuildView(CatalogListBuildView):
    build_path = "code/index.html"
    catalog_heading = ""
    page_description = "Open-source computer programming packages and projects"
    page_slug = "code"
    page_title = "Code"
    update_type = None

    def get_catalog(self) -> Sequence[CodeProject]:
        return load_code()

    def get_category_list(
        self,
        catalog: Sequence[App | CodeProject | Doc],
    ) -> Sequence[CodeCategory]:
        return group_code([item for item in catalog if isinstance(item, CodeProject)])


class GuideListBuildView(DocListBuildView):
    build_path = "guides/index.html"
    catalog_heading = ""
    doc_type = "lesson-plan"
    page_description = "Practical guides for data journalists"
    page_slug = "guides"
    page_title = "Guides"
    update_type = None


class DocsLandingBuildView(CanonicalBuildMixin, BuildableTemplateView):
    build_path = "docs/index.html"
    template_name = "coltrane/docs_landing.html"


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


class LatestPostsJsonBuildFeed(CanonicalBuildMixin, LatestPostsJsonFeed, BuildableMixin):
    build_path = "feeds/posts.json"
    feed_url = "/feeds/posts.json"

    @property
    def build_method(self) -> Callable[[], None]:
        return self.build

    def build(self) -> None:
        self.prep_directory(self.build_path)
        content = self.get(self.create_request(self.feed_url)).content
        self.build_file(self.get_output_path(self.build_path), content)


class RobotsBuildView(CanonicalBuildMixin, BuildableTemplateView):
    build_path = "robots.txt"
    content_type = "text/plain"
    template_name = "robots.txt"


class SecurityTxtBuildView(CanonicalBuildMixin, BuildableTemplateView):
    build_path = ".well-known/security.txt"
    content_type = "text/plain; charset=utf-8"
    template_name = "security.txt"


class LLMsTxtBuildView(CanonicalBuildMixin, BuildableTemplateView):
    build_path = "llms.txt"
    content_type = "text/plain; charset=utf-8"
    template_name = "llms.txt"


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
