# Models
from coltrane.models import Link

# Helpers
import os
import sys
import time
import urllib
import logging
from coltrane import utils
logger = logging.getLogger(__name__)
from django.utils.encoding import smart_unicode


class DeliciousClient(object):
    """
    A super-minimal delicious client.
    """
    lastcall = 0
    
    def __init__(self, username, password, method='v1'):
        self.username = username
        self.password = password
        self.method = method
    
    def __getattr__(self, method):
        return DeliciousClient(self.username, self.password, '%s/%s' % (self.method, method))
        
    def __repr__(self):
        return "<DeliciousClient: %s>" % self.username
        
    def get_latest_data(self):
        self.link_list = []
        self.xml = utils.getxml("http://delicious.com/v2/rss/palewire")
        for link in self.xml.getiterator("item"):
            title = smart_unicode(link.find('title').text)
            description = smart_unicode(link.find('description').text)
            url = smart_unicode(link.find('link').text)
            date = link.find('pubDate').text
            date = utils.parsedate(date)
            tags = getattr(link.find("category"), "text", "")
            d = dict(
                title=title,
                description=description,
                date=date,
                url=url,
                tags=tags,
            )
            self.link_list.append(d)
        return self.link_list 
    
    def sync(self):
        """
        When executed, will collect update your database with the latest books.
        """
        [self._handle_bookmark(d) for d in self.get_latest_data()]
    
    def _handle_bookmark(self, data):
        """
        Accept a data dictionary drawn from the Delicious API and syncs it to the database.
        """
        try:
            # Just test the URL in case it's already been logged by another bookmarking service like Delicious.
            l = Link.objects.get(url=data['url'])
            # And just quit out silently if it already exists.
            logger.debug("Link already exists for %s" % data["title"].encode("utf-8"))
        except Link.DoesNotExist:
            # If it doesn't exist, add it fresh.
            logger.debug("Adding link to %s" % data["title"].encode("utf-8"))
            l = Link(
                title=data['title'],
                description=data['description'],
                pub_date=data['date'],
                url=data['url'],
                tags=data['tags'],
            )
            l.save()

