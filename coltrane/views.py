import datetime

# Time
import time
from functools import lru_cache
from pathlib import Path

# Third-party
import markdown
import yaml
from django.conf import settings
from django.http import Http404, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.generic import ListView, TemplateView

# Helpers
from proxy.views import proxy_view

from coltrane.content_loaders import load_awards, load_bots, load_clips, load_docs, load_posts, load_talks

CONTENT_PATH = Path(__file__).resolve().parent / "content"


@lru_cache(maxsize=1)
def _load_bio_html():
    bio_path = CONTENT_PATH / "bio.md"
    bio_markdown = bio_path.read_text(encoding="utf-8")
    replacements = {
        "work_url": reverse("coltrane_work_list"),
        "doc_url": reverse("coltrane_doc_list"),
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
    date_stamp = time.strptime(year + month + day, "%Y%m%d")
    pub_date = datetime.date(*date_stamp[:3])
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


def server_error(request, template_name="500.html"):
    """
    500 error handler. Necessary to make sure STATIC_URL is available.
    """
    t = loader.get_template(template_name)
    return HttpResponseServerError(t.render({"STATIC_URL": settings.STATIC_URL}))


class ClipListView(TemplateView):
    template_name = "coltrane/clip_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = load_clips()
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
    template_name = "coltrane/doc_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_docs = load_docs()
        context["lesson_list"] = [d for d in all_docs if d.type == "lesson-plan"]
        context["software_list"] = [d for d in all_docs if d.type == "software"]
        return context


class BotListView(TemplateView):
    template_name = "coltrane/bot_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = load_bots()
        return context


#
# Mastodon
#


def wellknown_webfinger(request):
    remote_url = f"https://mastodon.palewi.re/.well-known/webfinger?{request.META['QUERY_STRING']}"
    return proxy_view(request, remote_url)


def wellknown_hostmeta(request):
    remote_url = f"https://mastodon.palewi.re/.well-known/host-meta?{request.META['QUERY_STRING']}"
    return proxy_view(request, remote_url)


def wellknown_nodeinfo(request):
    remote_url = "https://mastodon.palewi.re/.well-known/nodeinfo"
    return proxy_view(request, remote_url)


def username_redirect(request):
    return HttpResponseRedirect("https://mastodon.palewi.re/@palewire")
