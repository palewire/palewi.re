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


class NewsBlurClient(object):
    """
    A super-minimal NewsBlur client.
    """
    def __init__(self):
        self.url = 'http://palewire.newsblur.com/social/rss/11281/palewire'
    
    def __getattr__(self, method):
        return NewsBlurClient()
        
    def __repr__(self):
        return "<NewsBlurClient>"
        
    def get_latest_data(self):
        self.link_list = []
        self.xml = utils.getxml(self.url)
        for link in self.xml.getiterator("{http://www.w3.org/2005/Atom}entry"):
            title = smart_unicode(link.find('{http://www.w3.org/2005/Atom}title').text)
            url = smart_unicode(link.find('{http://www.w3.org/2005/Atom}link').get('href'))
            date = link.find('{http://www.w3.org/2005/Atom}updated').text
            date = utils.parsedate(date)
            d = dict(
                title=title,
                date=date,
                url=url,
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
                pub_date=data['date'],
                url=data['url'],
            )
            l.save()

