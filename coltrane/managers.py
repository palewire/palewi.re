from django.db import models


class LivePostManager(models.Manager):
    """
    Returns all posts set to be published.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(status=self.model.LIVE_STATUS)
