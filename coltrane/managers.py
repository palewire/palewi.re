import datetime
from django.db import models


class LivePostManager(models.Manager):
    """
    Returns all posts set to be published.
    """

    def get_queryset(self):
        qs = super(LivePostManager, self).get_queryset()
        return qs.filter(status=self.model.LIVE_STATUS)


class LiveCategoryManager(models.Manager):
    """
    Returns all categories with at least one live post.
    """

    def get_queryset(self):
        qs = super(LiveCategoryManager, self).get_queryset()
        return qs.filter(post_count__gt=0)


class SyncManager(models.Manager):
    """
    A set of utilities for working with the third-party models.
    """

    def get_last_update(self, **kwargs):
        """
        Return the last time a given model's items were updated. Returns the
        epoch if the items were never updated.
        """
        qs = self
        if kwargs:
            qs = self.filter(**kwargs)
        try:
            return qs.order_by("-pub_date")[0].pub_date
        except IndexError:
            return datetime.datetime.fromtimestamp(0)
