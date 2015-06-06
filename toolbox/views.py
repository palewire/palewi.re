from django.views.generic import TemplateView
from django.http import HttpResponse


def app_status(request):
    """
    Page for Varnish to check the server/app status
    """
    return HttpResponse("ok")


class DirectTemplateView(TemplateView):
    extra_context = None
    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        if self.extra_context is not None:
            for key, value in self.extra_context.items():
                if callable(value):
                    context[key] = value()
                else:
                    context[key] = value
        return context
