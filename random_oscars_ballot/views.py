import random
from models import Category, Nominee
from django.shortcuts import render
from django.views.decorators.cache import never_cache


@never_cache
def index(request):
    if request.GET.get("roll", None):
        pick_list = []
        for category in Category.objects.all():
            pick = random.choice(category.nominee_set.all())
            pick_list.append(dict(category=category.name, pick=pick.name))
        context = {'pick_list': pick_list}
    else:
        context = {}
    return render(request, 'random_oscars_ballot/index.html', context)

