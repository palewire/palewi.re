from django.http import JsonResponse


def health_check(request):
    """Confirm that Django can serve requests without external state."""
    return JsonResponse({"status": "ok"})
