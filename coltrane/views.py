# Helpers
import time
import datetime
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


def index(request):
    """
    The homepage of the site, which simply redirects to the bio.
    """
    try:
        latest_post = Post.live.latest()
        return HttpResponseRedirect(latest_post.get_absolute_url())
    except Post.DoesNotExist:
        return HttpResponseRedirect("/ticker/")


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


def ticker_detail(request, page=1, response_type='html'):
    """
    A tumble log of my latest online activity. Allows for filtering by content
    type.
    """
    # Available content type filters
    contenttypes_whitelist = [
        'beer',
        'book',
        'change',
        'commit',
        'link',
        'location',
        'movie',
        'photo',
        'shout',
        'track',
    ]

    # Check if the user has provided a filter
    filter_string = request.GET.get("filters")

    # If there's no filter, it's a lot easier
    object_list = Ticker.objects.all()
    selected_slugs = contenttypes_whitelist
    filtered = False

    # If there is a filter, piece it together using the content types
    if filter_string:
        filtered = True
        filter_list = filter_string.split(",")
        contenttype_list = []
        selected_slugs = []
        for filter in filter_list:
            if filter in contenttypes_whitelist:
                try:
                    selected_slugs.append(filter)
                    contenttype_list.append(
                        ContentType.objects.get(
                            app_label__in=['comments', 'coltrane', 'correx'],
                            name=filter
                        )
                    )
                except ContentType.DoesNotExist:
                    pass
        if not contenttype_list:
            raise Http404

        # Pull the data
        object_list = object_list.filter(content_type__in=contenttype_list)

    # Grab the first page of 100 items
    paginator = Paginator(object_list, 100)
    try:
        page_obj = paginator.page(int(page))
    except (EmptyPage, InvalidPage):
        raise Http404

    # Figure out what template to use
    templates = {
        'html': 'coltrane/ticker_list.html',
        'json': 'coltrane/ticker_list.json',
    }
    template = templates[response_type]

    # Figure out the content type for the response
    content_types = {
        'html': 'text/html',
        'json': 'text/javascript',
    }
    content_type = content_types[response_type]

    # Pass out the data
    context = {
        "object_list": list(page_obj.object_list.fetch_generic_relations()),
        "page": page_obj,
        "selected_slugs": selected_slugs,
        "filtered": filtered,
    }
    return render(request, template, context, content_type=content_type)


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


def category_detail(request, slug):
    """
    A list that reports all the posts in a particular category.
    """
    category = get_object_or_404(Category, slug=slug)
    context = dict(
        object_list=category.post_set.all(),
        category=category,
    )
    return render(request, 'coltrane/category_detail.html', context)


def correx_redirect(request, id):
    """
    Redirect the browser to the content object page where a
    particular correction is published.
    """
    correction = get_object_or_404(Change, id=id)
    content_object = correction.get_content_object()
    if not content_object:
        raise Http404
    return HttpResponseRedirect(content_object.get_absolute_url())


def newtwitter_pagination_index(request):
    """
    An index page where we can lay out how to pull off Twitter style
    pagination.

    Passed out the 100 latest tracks to seed the page.
    """
    # Pull the data
    object_list = Track.objects.all()

    # Grab the first page of 100 items
    paginator = Paginator(object_list, 100)
    page_obj = paginator.page(1)

    # Pass out the data
    context = {
        "object_list": page_obj.object_list,
        "page": page_obj,
    }
    template = 'tutorials/newtwitter_pagination/index.html'
    return render(request, template, context)


def newtwitter_pagination_json(request, page):
    """
    A JSON feed to feed updates to the index page as the user
    scrolls down the page.

    Passes out pages of Track objects based on the `page` kwarg.
    """
    # Pull the data
    object_list = Track.objects.all()

    # Pull the proper items for this page
    paginator = Paginator(object_list, 100)
    try:
        page_obj = paginator.page(page)
    except InvalidPage:
        # Return 404 if the page doesn't exist
        raise Http404

    # Pass out the data
    context = {
        "object_list": page_obj.object_list,
        "page": page_obj,
    }
    template = 'tutorials/newtwitter_pagination/tracks.json'
    return render(request, template, context, content_type='text/javascript')


def server_error(request, template_name='500.html'):
    """
    500 error handler. Necessary to make sure STATIC_URL is available.
    """
    t = loader.get_template(template_name)
    return HttpResponseServerError(t.render(Context({
        'MEDIA_URL': settings.MEDIA_URL,
        'STATIC_URL': settings.STATIC_URL,
    })))
