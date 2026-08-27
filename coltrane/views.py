from datetime import date
from functools import lru_cache
from pathlib import Path

# Third-party
import markdown
import yaml
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.generic import ListView, TemplateView

from coltrane.content_loaders import (
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

CONTENT_PATH = Path(__file__).resolve().parent / "content"


@lru_cache(maxsize=1)
def _load_bio_html():
    bio_path = CONTENT_PATH / "bio.md"
    bio_markdown = bio_path.read_text(encoding="utf-8")
    replacements = {
        "clips_url": reverse("coltrane_clip_list"),
        "code_url": reverse("coltrane_code_list"),
        "guides_url": reverse("coltrane_guide_list"),
        "talk_url": reverse("coltrane_talk_list"),
    }
    bio_markdown = bio_markdown.format(**replacements)
    return markdown.markdown(bio_markdown, extensions=["extra"])


def _load_yaml_list(path, key):
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    values = data.get(key, [])
    return values if isinstance(values, list) else []


BIO_EMAIL_LIST = _load_yaml_list(CONTENT_PATH / "bio_meta.yaml", "emails")
BIO_SKILL_LIST = _load_yaml_list(CONTENT_PATH / "bio_skills.yaml", "skills")
BIO_SOCIAL_LIST = _load_yaml_list(CONTENT_PATH / "bio_meta.yaml", "socials")


def bio(request):
    """
    All about Ben.
    """
    context = {
        "bio_html": mark_safe(_load_bio_html()),
        "award_list": load_awards(),
        "socialmedia_list": BIO_SOCIAL_LIST,
        "email_list": BIO_EMAIL_LIST,
        "skill_list": BIO_SKILL_LIST,
    }
    return render(request, "coltrane/bio.html", context)


def post_detail(request, year, month, day, slug):
    """
    A detail page that shows an entire post.
    """
    try:
        pub_date = date.fromisoformat(f"{year}-{month}-{day}")
    except ValueError as error:
        raise Http404 from error
    post = next(
        (
            candidate
            for candidate in load_posts()
            if candidate.published_at.date() == pub_date and candidate.slug == slug
        ),
        None,
    )
    if post is None:
        raise Http404
    context = {
        "object": post,
    }
    return render(request, "coltrane/post_detail.html", context)


class ClipListView(TemplateView):
    template_name = "coltrane/clip_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = [clip for clip in load_clips() if clip.type in {"app", "story"}]
        return context


class AppListView(TemplateView):
    template_name = "coltrane/catalog_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        catalog = load_apps()
        context.update(
            {
                "catalog_heading": "",
                "category_list": group_apps(catalog),
                "object_list": catalog,
                "page_description": "My independent network of Internet publications",
                "page_slug": "apps",
                "page_title": "Apps",
                "update_list": load_clip_updates("service", catalog),
                "updates_heading": "Updates",
            }
        )
        return context


class TalkListView(TemplateView):
    template_name = "coltrane/talk_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = load_talks()
        return context


class PostListView(ListView):
    template_name = "coltrane/post_list.html"

    def get_queryset(self):
        return load_posts()


class DocListView(TemplateView):
    template_name = "coltrane/catalog_list.html"
    catalog_heading: str
    doc_type: str
    page_description: str
    page_slug: str
    page_title: str
    updates_heading = "Updates"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        catalog = [doc for doc in load_docs() if doc.type == self.doc_type]
        context.update(
            {
                "catalog_heading": self.catalog_heading,
                "object_list": catalog,
                "page_description": self.page_description,
                "page_slug": self.page_slug,
                "page_title": self.page_title,
                "update_list": load_clip_updates(self.doc_type, catalog),
                "updates_heading": self.updates_heading,
            }
        )
        return context


class CodeListView(TemplateView):
    template_name = "coltrane/catalog_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        catalog = load_code()
        context.update(
            {
                "catalog_heading": "",
                "category_list": group_code(catalog),
                "object_list": catalog,
                "page_description": "Open-source computer programming packages and projects",
                "page_slug": "code",
                "page_title": "Code",
                "update_list": [],
            }
        )
        return context


class GuideListView(DocListView):
    catalog_heading = ""
    doc_type = "lesson-plan"
    page_description = "Practical guides for data journalists"
    page_slug = "guides"
    page_title = "Guides"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["update_list"] = []
        return context


class BotListView(TemplateView):
    template_name = "coltrane/bot_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = load_bots()
        return context


def username_redirect(request):
    return HttpResponseRedirect("https://mastodon.palewi.re/@palewire")
