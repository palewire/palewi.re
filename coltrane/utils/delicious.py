# Models
from coltrane.models import Link

# Helpers
import os
import sys
import time
import urllib
from qiklog import QikLog
from coltrane import utils
from django.utils.encoding import smart_unicode


class DeliciousClient(object):
    """
    A super-minimal delicious client.
    """
    logger = QikLog("coltrane.utils.delicious")
    lastcall = 0
    
    def __init__(self, username, password, method='v1'):
        self.username = username
        self.password = password
        self.method = method
    
    def __getattr__(self, method):
        return DeliciousClient(self.username, self.password, '%s/%s' % (self.method, method))
        
    def __repr__(self):
        return "<DeliciousClient: %s>" % self.username
        
    def __call__(self, **params):
        # Enforce Yahoo's "no calls quicker than every 1 second" rule
        delta = time.time() - self.lastcall
        if delta < 2:
            time.sleep(4 - delta)
        self.lastcall = time.time()
        url = ("https://api.del.icio.us/%s?" % self.method) + urllib.urlencode(params)
        xml = utils.getxml(url, username=self.username, password=self.password)
        return xml

    def sync(self):
        """
        Updates Delicious data and syncs it to the Link model.
        """
        # Init an empty link list we'll fill up
        self.link_list = []
        # Check to see if which posts might need an update.
        self.last_update_date = Link.sync.get_last_update()
        self.date_list = reversed(list(self.posts.dates().getiterator('date')))
        for datenode in self.date_list:
            dt = utils.parsedate(datenode.get("date"))
            # If the date in the record is the same or newer than the date of the last update..
            if dt.date() >= self.last_update_date.date():
                # Fetch all the posts on that date
                [self.link_list.append(i) for i in self._fetch_links_by_date(dt)]
        # Handle all the bookmarks from valid days
        [self._handle_bookmark(i) for i in self.link_list]

    def _fetch_links_by_date(self, dt):
        """
        Retrieves and processes all posts from the submitted date.
        """
        link_list = []
        self.logger.log.debug("Reading bookmarks from %s", dt)
        # Grab all the posts
        xml = self.posts.get(dt=dt.strftime("%Y-%m-%d")).getiterator('post')
        # Loop through them
        for post in xml:
            # Pull out all the attributes into a dictionary.
            data = dict((k, smart_unicode(post.get(k))) for k in post.keys())
            link_list.append(data)
        return link_list
    
    def _handle_bookmark(self, data):
        """
        Accept a data dictionary drawn from the Delicious API and syncs it to the database.
        """
        try:
            # Just test the URL in case it's already been logged by another bookmarking service like Delicious.
            l = Link.objects.get(url=data['href'])
            # And just quit out silently if it already exists.
            self.logger.log.debug("Link already exists for %s" % data["description"])
        except Link.DoesNotExist:
            # If it doesn't exist, add it fresh.
            self.logger.log.debug("Adding link to %s" % data["description"])
            l = Link(
                url = data['href'],
                title = data['description'],
                description = data.get('extended', ''),
                pub_date = utils.parsedate(str(data['time'])),
                tags = data['tag']
            )
            l.save()

