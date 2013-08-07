from django.contrib.sites.models import Site
from django.http import HttpResponsePermanentRedirect
from django.core.urlresolvers import resolve
from django.core import urlresolvers
from django.utils.http import urlquote


class MultipleProxyMiddleware(object):
    FORWARDED_FOR_FIELDS = [
        'HTTP_X_FORWARDED_FOR',
        'HTTP_X_FORWARDED_HOST',
        'HTTP_X_FORWARDED_SERVER',
    ]

    def process_request(self, request):
        """
        Rewrites the proxy headers so that only the most
        recent proxy is used.
        """
        for field in self.FORWARDED_FOR_FIELDS:
            if field in request.META:
                if ',' in request.META[field]:
                    parts = request.META[field].split(',')
                    request.META[field] = parts[-1].strip()


class DomainRedirectMiddleware(object):
    """
    Redirect traffic to all sibling domains to http://palewi.re
    """
    host = 'palewi.re'
    
    def update_uri(self, request):
        return '%s://%s%s%s' % (
            request.is_secure() and 'https' or 'http',
            self.host,
            urlquote(request.path),
            (request.method == 'GET' and len(request.GET) > 0) and '?%s' % request.GET.urlencode() or ''
        )
    
    def process_request(self, request):
        host = request.get_host()
        if host == 'www.palewire.com':
            new_uri = self.update_uri(request)
            return HttpResponsePermanentRedirect(new_uri)
        elif host == "palewire.com":
            new_uri = self.update_uri(request)
            return HttpResponsePermanentRedirect(new_uri)
