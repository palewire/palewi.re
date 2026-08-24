from urllib.parse import quote

from django.http import HttpResponsePermanentRedirect


class DomainRedirectMiddleware:
    """
    Redirect traffic to all sibling domains to http://palewi.re
    """

    host = "palewi.re"

    def update_uri(self, request):
        return "%s://%s%s%s" % (
            "https" if request.is_secure() else "http",
            self.host,
            quote(request.path),
            (request.method == "GET" and len(request.GET) > 0) and "?%s" % request.GET.urlencode() or "",
        )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        if host in ["www.palewire.com", "palewire.com", "www.palewi.re"]:
            new_uri = self.update_uri(request)
            return HttpResponsePermanentRedirect(new_uri)

        return self.get_response(request)
