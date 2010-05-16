# Helpers
import datetime

# Models
from coltrane.models import *


class LivePostManager(models.Manager):
    """
    Returns all posts set to be published.
    """
    
    def get_query_set(self):
        return super(LivePostManager, self).get_query_set().filter(status=self.model.LIVE_STATUS)


class LiveCategoryManager(models.Manager):
    """
    Returns all categories with at least one live post.
    """

    def get_query_set(self):
        return super(LiveCategoryManager, self).get_query_set().filter(post_count__gt=0)


class LinkDomainManager(models.Manager):
    """
    Returns an analysis of the domain names found in the Link model.
    
    The result is formed as a list of tuples, with the domain first and count second.
    """
    
    def rank(self):
        """
        All domains in the Link model, ranked from greatest to least.
        """
        from urlparse import urlparse
        
        # Fetch all the domains
        domains = [urlparse(i.url)[1] for i in self.all()]
        
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
        domain_tuple.sort(lambda x,y:cmp(x[1], y[1]))
        domain_tuple.reverse()
        
        # Pass out the results
        return domain_tuple



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
        GROUP BY tag_id
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


