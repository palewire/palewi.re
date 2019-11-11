# Helpers
import time
import datetime
from django.conf import settings
from django.views.generic import ListView
from django.template import Context, loader
from django.http import HttpResponseServerError
from django.shortcuts import get_object_or_404, render

# Models
from coltrane.models import Post
from bona_fides import models as bona_fides


def bio(request):
    """
    All about Ben.
    """
    context = {
        'award_list': bona_fides.Award.objects.all(),
        'socialmedia_list': bona_fides.SocialMediaProfile.objects.all(),
        'skill_list': bona_fides.Skill.objects.all(),
    }
    return render(request, 'coltrane/bio.html', context)


def post_detail(request, year, month, day, slug):
    """
    A detail page that shows an entire post.
    """
    date_stamp = time.strptime(year+month+day, "%Y%m%d")
    pub_date = datetime.date(*date_stamp[:3])
    post = get_object_or_404(
        Post,
        pub_date__year=pub_date.year,
        pub_date__month=pub_date.month,
        pub_date__day=pub_date.day,
        slug=slug
    )
    context = {
        'object': post,
    }
    return render(request, 'coltrane/post_detail.html', context)


def server_error(request, template_name='500.html'):
    """
    500 error handler. Necessary to make sure STATIC_URL is available.
    """
    t = loader.get_template(template_name)
    return HttpResponseServerError(t.render(Context({
        'MEDIA_URL': settings.MEDIA_URL,
        'STATIC_URL': settings.STATIC_URL,
    })))


class ClipListView(ListView):
    model = bona_fides.Clip
    template_name = "coltrane/clip_list.html"


class TalkListView(ListView):
    model = bona_fides.Talk
    template_name = "coltrane/talk_list.html"


class PostListView(ListView):
    queryset = Post.live.all().order_by("-pub_date")
