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
    A set of utilities for working with the Track model.
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


class GFKManager(models.Manager):
    """
    A manager that returns a GFKQuerySet instead of a regular QuerySet.

    """
    def get_queryset(self):
        return GFKQuerySet(self.model)


class GFKQuerySet(QuerySet):
    """
    A QuerySet with a fetch_generic_relations() method to bulk fetch
    all generic related items.  Similar to select_related(), but for
    generic foreign keys.

    Based on http://www.djangosnippets.org/snippets/984/
    Firstly improved at http://www.djangosnippets.org/snippets/1079/

    """
    def fetch_generic_relations(self):
        qs = self._clone()

        gfk_fields = [g for g in self.model._meta.virtual_fields if isinstance(g, GenericForeignKey)]

        ct_map = {}
        item_map = {}
        data_map = {}

        for item in qs:
            for gfk in gfk_fields:
                ct_id_field = self.model._meta.get_field(gfk.ct_field).column
                ct_map.setdefault(
                    (getattr(item, ct_id_field)), {}
                    )[getattr(item, gfk.fk_field)] = (gfk.name, item.id)
            item_map[item.id] = item

        for (ct_id), items_ in ct_map.items():
            if (ct_id):
                ct = ContentType.objects.get_for_id(ct_id)
                for o in ct.model_class().objects.select_related().filter(id__in=items_.keys()).all():
                    (gfk_name, item_id) = items_[o.id]
                    data_map[(ct_id, o.id)] = o

        for item in qs:
            for gfk in gfk_fields:
                if (getattr(item, gfk.fk_field) != None):
                    ct_id_field = self.model._meta.get_field(gfk.ct_field).column
                    setattr(item, gfk.name, data_map[(getattr(item, ct_id_field), getattr(item, gfk.fk_field))])

        return qs
