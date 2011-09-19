# Helpers
import time
import datetime
from django.shortcuts import render_to_response, get_object_or_404
from django.http import Http404, HttpResponseRedirect
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse

# Models
from correx.models import Change
from django.db.models import get_model
from tagging.models import Tag, TaggedItem
from django.contrib.contenttypes.models import ContentType
from coltrane.models import Post, Category, Link, Photo, Track, Ticker

# Generic Views
from django.views.generic.list_detail import object_list
from django.views.generic.simple import direct_to_template


def index(request):
    """
    The homepage of the site, which simply redirects to the latest post.
    """
    latest_post = Post.live.latest()
    return HttpResponseRedirect(latest_post.get_absolute_url())


def ticker_detail(request, page):
    """
    A tumble log of my latest online activity. Allows for filtering by content
    type.
    """
    # Available content type filters
    contenttypes_whitelist = [
        'book',
        'change',
        'comment',
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
        if len(filter_list) == len(contenttypes_whitelist):
            return HttpResponseRedirect("/ticker/page/1/")
        contenttype_list = []
        selected_slugs = []
        for filter in filter_list:
            if filter in contenttypes_whitelist:
                try:
                    selected_slugs.append(filter)
                    contenttype_list.append(ContentType.objects.get(app_label__in=['comments', 'coltrane'], name=filter))
                except ContentType.DoesNotExist:
                    raise Http404
        # Pull the data
        object_list = object_list.filter(content_type__in=contenttype_list)

    # Grab the first page of 100 items
    paginator = Paginator(object_list, 50)
    try:
        page_obj = paginator.page(int(page))
    except (EmptyPage, InvalidPage):
        raise Http404
    
    # Pass out the data
    context = {
        "object_list": page_obj.object_list,
        "page": page_obj,
        "selected_slugs": selected_slugs,
        "filtered": filtered,
    }
    template = 'coltrane/ticker_list.html'
    return direct_to_template(request, template, context)



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
    related_posts = TaggedItem.objects.get_related(post, get_model('coltrane', 'post'))[:5]
    context = {
        'object': post,
        'related_posts': related_posts
    }
    return direct_to_template(request, 'coltrane/post_detail.html', context)


def category_detail(request, slug):
    """
    A list that reports all the posts in a particular category.
    """
    category = get_object_or_404(Category, slug=slug)
    return object_list(request, queryset = category.post_set.all(), 
                        extra_context = {'category': category },
                        template_name = 'coltrane/category_detail.html')


def tag_detail(request, tag):
    """
    A list that reports all of the content with a particular tag.
    """
    try:
        tag = Tag.objects.get(name=tag)
    except Tag.DoesNotExist:
        # If the tag isn't found, try it with hyphens removed, which
        # was the convention on my old Wordpress blog. This can help
        # keep old tag page links alive.
        try:
            tag = Tag.objects.get(name=tag.replace("-", ""))
        except Tag.DoesNotExist:
            raise Http404
    
    # Pull all the items with that tag.
    taggeditem_list = tag.items.all()
    
    # Loop through the tagged items and return just the items
    object_list = [i.object for i in taggeditem_list if getattr(i.object, 'pub_date', False)]
    
    # Now resort them by the pub_date attribute we know each one should have
    object_list.sort(key=lambda x: x.pub_date, reverse=True)

    # Pass it out
    return direct_to_template(request, 'coltrane/tag_detail.html', { 
            'tag': tag, 
            'object_list': object_list,
        })


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
    template = 'newtwitter_pagination/index.html'
    return direct_to_template(request, template, context)


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
    template = 'newtwitter_pagination/tracks.json'
    return direct_to_template(request, template, context, 'text/javascript')

