# Utils
import os
from django.http import Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic.simple import direct_to_template

# Models
from rapture.update.models import *
from rapture.data.models import *


def get_data_dict():
    """
    A reusable function that pulls data from the Score field and loads it in a dictionary.
    """
    score_list = Score.objects.all().order_by('edition', 'category')
    return dict(score_list=score_list)

def csv(request):
    return render_to_response('rapture/data/scores.csv', get_data_dict(), mimetype="text/javascript")

def json(request):
    return render_to_response('rapture/data/scores.json', get_data_dict(), mimetype="text/javascript")

def xml(request):
    return render_to_response('rapture/data/scores.xml', get_data_dict(), mimetype="text/javascript")
    
def xls(request):
    """
    A method for exporting to Microsoft Excel lifted from "DjangoSnippet #911":http://www.djangosnippets.org/snippets/911/
    """
    response = render_to_response("rapture/data/scores.html", get_data_dict())
    response['Content-Disposition'] = 'attachment; filename=scores.xls'
    response['Content-Type'] = 'application/vnd.ms-excel; charset=utf-8'
    return response
