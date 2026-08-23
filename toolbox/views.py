import logging

from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)


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


def health_check(request):
    """Lightweight health endpoint that verifies the database is reachable."""
    try:
        connection.ensure_connection()
        db_ok = True
    except DatabaseError:
        logger.exception("Database health check failed")
        db_ok = False

    status = 200 if db_ok else 503
    return JsonResponse({"status": "ok" if db_ok else "error", "db": db_ok}, status=status)
