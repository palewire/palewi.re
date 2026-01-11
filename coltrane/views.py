from functools import lru_cache
from pathlib import Path

# Time
import time
import datetime

# Third-party
import markdown
import yaml

# Helpers
from proxy.views import proxy_view
from django.conf import settings
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.views.generic import ListView, TemplateView
from django.template import Context, loader
from django.http import HttpResponseServerError, Http404, HttpResponseRedirect
from django.urls import reverse

# Models
from coltrane.models import Post
from bona_fides import models as bona_fides


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


def bio(request):
    """
    All about Ben.
    """
    context = {
        "bio_html": mark_safe(_load_bio_html()),
        "award_list": bona_fides.Award.objects.all(),
        "socialmedia_list": bona_fides.SocialMediaProfile.objects.all(),
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
    try:
        post = Post.live.get(
            pub_date__year=pub_date.year,
            pub_date__month=pub_date.month,
            pub_date__day=pub_date.day,
            slug=slug,
        )
    except Post.DoesNotExist:
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
    return HttpResponseServerError(
        t.render(
            Context(
                {
                    "MEDIA_URL": settings.MEDIA_URL,
                    "STATIC_URL": settings.STATIC_URL,
                }
            )
        )
    )


class ClipListView(ListView):
    model = bona_fides.Clip
    template_name = "coltrane/clip_list.html"


class TalkListView(ListView):
    model = bona_fides.Talk
    template_name = "coltrane/talk_list.html"


class PostListView(ListView):
    queryset = Post.live.all().order_by("-pub_date")


class DocListView(TemplateView):
    template_name = "coltrane/doc_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson_list"] = bona_fides.Doc.objects.filter(type="lesson-plan")
        context["software_list"] = bona_fides.Doc.objects.filter(type="software")
        return context


class BotListView(TemplateView):
    template_name = "coltrane/bot_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = [
            dict(
                title="@DivineAnnDvorak",
                twitter_url="https://twitter.com/divineanndvorak",
                mastodon_url="https://mastodon.palewi.re/@divineanndvorak",
            ),
            dict(
                title="@LAXweather",
                twitter_url="https://twitter.com/laxweatherbot",
                mastodon_url="https://mastodon.palewi.re/@laxweather",
            ),
            dict(
                title="@MuckRockBot",
                twitter_url="https://twitter.com/muckrockbot",
                mastodon_url="https://mastodon.palewi.re/@muckrockbot",
            ),
            dict(
                title="@NewsHomepages",
                twitter_url="https://twitter.com/newshomepages",
                mastodon_url="https://mastodon.palewi.re/@newshomepages",
            ),
            dict(
                title="@NYCDataBot",
                mastodon_url="https://mastodon.palewi.re/@nycdatabot",
            ),
            dict(
                title="@OldLAPhotos",
                twitter_url="https://twitter.com/oldlaphotos",
                mastodon_url="https://mastodon.palewi.re/@oldlaphotos",
            ),
            dict(
                title="@RandomPigeonGPT",
                mastodon_url="https://mastodon.palewi.re/@RandomPigeonGPT",
            ),
            dict(
                title="@ReutersJobs",
                twitter_url="https://twitter.com/reutersjobs",
                mastodon_url="https://mastodon.palewi.re/@ReutersJobs",
            ),
            dict(
                title="@SanbornMaps",
                twitter_url="https://twitter.com/sanbornmaps",
                mastodon_url="https://mastodon.palewi.re/@sanbornmaps",
            ),
        ]
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
