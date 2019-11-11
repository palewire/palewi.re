# Helpers
import time
import datetime
from django.views.generic.list import ListView
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.http import Http404, HttpResponseRedirect, HttpResponseServerError
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.template import Context, loader
from django.views.generic import ListView

# Models
from correx.models import Change
from bona_fides import models as bona_fides
from django.contrib.contenttypes.models import ContentType
from coltrane.models import Post, Category, Link, Photo, Track, Ticker, Beer
from bona_fides.models import Clip, Talk


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
    post = get_object_or_404(Post,
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
    model = Clip
    template_name = "coltrane/clip_list.html"


class TalkListView(ListView):
    model = Talk
    template_name = "coltrane/talk_list.html"


class PostListView(ListView):
    queryset = Post.live.all().order_by("-pub_date")
