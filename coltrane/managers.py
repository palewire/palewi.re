import datetime
from django.db import models
from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey


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


class TopDomainUpdateManager(models.Manager):
    """
    Updates the TopDomain model with the latest totals
    """
    def ranking(self, count=50, min_count=3, strata=6):
        from urlparse import urlparse
        from coltrane.models import Link
        from coltrane.utils.cloud import calculate_cloud

        # Fetch all the domains
        domains = [urlparse(i.url)[1] for i in Link.objects.all()]

        # Create a dict to stuff the counts
        domain_count = {}

        # Loop through all the domains
        for d in domains:
            try:
                # If it exists in the dict, bump it up one
                domain_count[d]['count'] += 1
            except KeyError:
                # If it doesn't exist yet, add it to the dict
                domain_count[d] = {'count': 1, 'font-size': None}

        # Sort the results as a list of tuples, from top to bottom
        domain_tuple = domain_count.items()
        domain_tuple.sort(lambda x,y:cmp(x[1], y[1]), reverse=True)

        # Slice the limit and convert it to a dictionary
        domain_dict = dict(domain_tuple[:count])

        # Pass it into the cloud
        object_list = calculate_cloud(
            domain_dict, steps=strata, min_count=min_count, qs=False
        )

        # Empty out the model and refill it with the new data
        self.model.objects.all().delete()
        for obj in object_list:
            self.model.objects.create(
                name=obj['tag'],
                count=obj['count'],
                stratum=obj['font_size']
            )
        return True



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


class TopTagUpdateManager(models.Manager):
    """
    Updates the TopTag model with the latest totals
    """

    def ranking(self, count=100, strata=6):
        """
        Refills the TopTag model with the most-commonly applied tags, using
        the provided count value as its cut-off.
        """
        from django.db import connection
        from tagging.models import TaggedItem, Tag
        from coltrane.utils.cloud import calculate_cloud

        # Pull the cloud data, excluding tracks
        sql = """
        SELECT t.name, count(*)
        FROM tagging_taggeditem as ti
        INNER JOIN tagging_tag as t ON ti.tag_id = t.id
        WHERE ti.content_type_id
        NOT IN (SELECT id FROM django_content_type WHERE name = 'track')
        GROUP BY t.name
        ORDER BY 2 DESC
        LIMIT %s;
        """ % count
        cursor = connection.cursor()
        cursor.execute(sql)
        tag_counts = {}
        for row in cursor.fetchall():
            tag_counts[row[0]] = {'count': row[1], 'font-size': None}

        # Pass it into the cloud
        object_list = calculate_cloud(tag_counts, steps=strata, qs=False)

        # Empty out the model and refill it with the new data
        self.model.objects.all().delete()
        for obj in object_list:
            tag = Tag.objects.get(name=obj['tag'])
            self.model.objects.create(
                tag=tag,
                name=obj['tag'],
                count=obj['count'],
                stratum=obj['font_size']
            )
        return True


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
