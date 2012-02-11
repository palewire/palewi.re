from django.contrib.sites.models import Site
from django.http import HttpResponsePermanentRedirect
from django.core.urlresolvers import resolve
from django.core import urlresolvers
from django.utils.http import urlquote


class WWWDomainRedirectMiddleware(object):
    def process_request(self, request):
        host = request.get_host()
        if host == 'www.palewire.com':
            host = 'palewire.com'
            new_uri = '%s://%s%s%s' % (
                request.is_secure() and 'https' or 'http',
                host,
                urlquote(request.path),
                (request.method == 'GET' and len(request.GET) > 0) and '?%s' % request.GET.urlencode() or ''
            )
            return HttpResponsePermanentRedirect(new_uri)
