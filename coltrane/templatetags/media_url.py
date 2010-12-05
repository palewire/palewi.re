from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def media_url(url_string):
    """
    Returns the media_url.

    Example:
    {% load media_url %}
    {% media_url "css/style.css" %}
    """
    return settings.MEDIA_URL + url_string
