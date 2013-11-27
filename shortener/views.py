import logging
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404, get_list_or_404, render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.http import HttpResponsePermanentRedirect
from django.utils import simplejson
from django.views.decorators.http import require_POST
from django.db import transaction
from django.conf import settings
from baseconv import base62
from models import Link, LinkSubmitForm


def follow(request, base62_id):
    """ 
    View which gets the link for the given base62_id value
    and redirects to it.
    """
    key = base62.to_decimal(base62_id)
    link = get_object_or_404(Link, pk=key)
    link.usage_count += 1
    link.save()
    return HttpResponsePermanentRedirect(link.url)


def submit(request):
    """
    View for submitting a URL
    """
    if not request.user.is_authenticated():
        # TODO redirect to an error page
        raise Http404
    link_form = None
    if request.GET:
        link_form = LinkSubmitForm(request.GET)
    elif request.POST:
        link_form = LinkSubmitForm(request.POST)
    if link_form and link_form.is_valid():
        url = link_form.cleaned_data['u']
        link, created = Link.objects.get_or_create(url=url)
        return HttpResponse(
            simplejson.dumps({
                "link": link.short_url(),
                "created": created,
            }),
            content_type='text/javascript'
        )
    return HttpResponse(status=400)


def index(request):
    """
    View for main page (lists recent and popular links)
    """
    if not request.user.is_authenticated():
        # TODO redirect to an error page
        raise Http404
    values = {}
    values['recent_links'] = Link.objects.all().order_by('-date_submitted')[0:10]
    values['most_popular_links'] = Link.objects.all().order_by('-usage_count')[0:10]
    return render(request, 'shortener/index.html', values)
