from datetime import date
from models import FreeFluVaccine
from django.shortcuts import render


def index(request):
    obj_list = FreeFluVaccine.objects.filter(date__gte=date.today())
    context = {
        'object_list': obj_list,
    }
    return render(request, "wxwtf/flushots/index.html", context)
