from datetime import datetime
from django.contrib.sites.models import Site


def current_site(request):
    """
    Add the "current site" to the template context.
    """
    try:
        return {
            'current_site': Site.objects.get_current()
        }
    except Site.DoesNotExist:
        return {'current_site':''}


def now(request):
    return {"now": datetime.now()}
