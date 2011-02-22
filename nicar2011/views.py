from django.shortcuts import get_object_or_404, render_to_response
from models import Project, Vote
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.db.models import Sum


def index(request):
    projects = Project.objects.all().order_by('-pub_date')[:5]
    return render_to_response('nicar2011/index.html', {'projects': projects})


def detail(request, poll_id):
    p = Project.objects.get(pk=poll_id)
    total = p.vote_set.count()
    return render_to_response('nicar2011/detail.html', {'project': p, 'vote_total': total, })


def vote(request, poll_id):
    p = get_object_or_404(Project, pk=poll_id)
    val = request.POST.get("data", None)
    if not val:
        val = request.GET.get("data", None) 
    if val == "0":
        value = -1
    else:
        value = 1
    v = p.vote_set.create(choice = value)
    v.save()
    return HttpResponse(status=200)


def data(request, poll_id):
    p = Project.objects.get(pk=poll_id)
    total = p.vote_set.aggregate(Sum('choice'))
    return render_to_response('nicar2011/data.xml', {'project': p, 'vote_total': total['choice__sum'], }, mimetype="text/xml")


def crossdomain(request):
    return HttpResponse('<?xml version=\"1.0\"?><cross-domain-policy><allow-access-from domain=\"*\" /></cross-domain-policy>', mimetype="text/xml")

