from django.db import models


class LivePostManager(models.Manager):
    """
    Returns all posts set to be published.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(status=self.model.LIVE_STATUS)


class LiveCategoryManager(models.Manager):
    """
    Returns all categories with at least one live post.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(post_count__gt=0)
