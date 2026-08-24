from datetime import datetime


def current_site(_request):
    """
    Add the current site to the template context.
    """
    return {"current_site": "palewi.re"}


def now(request):
    return {"now": datetime.now()}
