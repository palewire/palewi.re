import datetime
from django.db import models
from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class LivePostManager(models.Manager):
    """
    Returns all posts set to be published.
    """
    def get_queryset(self):
        return super(LivePostManager, self).get_queryset().filter(status=self.model.LIVE_STATUS)


class LiveCategoryManager(models.Manager):
    """
    Returns all categories with at least one live post.
    """
    def get_queryset(self):
        return super(LiveCategoryManager, self).get_queryset().filter(post_count__gt=0)



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
            return qs.order_by('-pub_date')[0].pub_date
        except IndexError:
            return datetime.datetime.fromtimestamp(0)
