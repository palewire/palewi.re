import os
import sys

# Set the directories and django config so it can be run from cron.
current_dir = os.path.abspath(__file__)
projects_dir = os.sep.join(current_dir.split(os.sep)[:-3])
os.environ['PYTHONPATH'] = projects_dir
sys.path.append(projects_dir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# Date and text manipulation
import time
import datetime
import dateutil.parser
from coltrane import utils
from django.utils.text import get_text_list
from django.utils.encoding import smart_unicode

# Logging
import logging
log = logging.getLogger("coltrane.utils.foursquare")

# Local application
from django.conf import settings
from coltrane.models import Location


class FoursquareClient(object):
    """
    A minimal Foursquare client. 
    """
    
    def __init__(self, url):
        self.url = url
        
    def __getattr__(self):
        return FoursquareClient(self.username)
        
    def __repr__(self):
        return "<FoursquareClient: %s>" % self.username
        
    def __call__(self):
        xml = utils.getxml(self.url)
        location_list = []
        for checkin in xml.getiterator("item"):
            title = smart_unicode(checkin.find('title').text)
            description = smart_unicode(checkin.find('description').text)
            url = smart_unicode(checkin.find('link').text)
            date = checkin.find('pubDate').text
            date = dateutil.parser.parse(date)
            location_dict = dict(
                title=title,
                description=description,
                date=date,
                url=url,
            )
            location_list.append(location_dict)
        return location_list


def enabled():
    """
    Test whether the necessary settings are in place.
    """
    ok = hasattr(settings, 'FOURSQUARE_RSS')
    if not ok:
        log.warn('The Foursquare provider is not available because the FOURSQUARE_RSS is undefined.')
    return ok


def update(diggs_to_fetch=10):
    """
    When executed, will collect update your database with the latest books.
    """
    # Init the DiggClient
    foursquare = FoursquareClient(settings.FOURSQUARE_RSS)
    
    # Fetch the data
    foursquare_data = foursquare()
    
    # Now loop through the data and add the new ones.
    [_handle_location(location_dict) for location_dict in foursquare_data]
        
        
def _handle_location(d):
    """
    Accepts a data dictionary harvest from Foursquare's API and logs 
    any new ones in the database.
    """
    try:
        # Just test the URL in case it's already been logged by another bookmarking service like Delicious.
        l = Location.objects.get(title=d['title'], pub_date=d['date'])
        # And just quit out silently if it already exists.
        log.debug("Location already exists for %s" % d["title"])
    
    except Location.DoesNotExist:
        # If it doesn't exist, add it fresh.
        log.debug("Adding location to %s" % d["title"])
        
        l = Location(
            url = d['url'],
            title = d['title'],
            description = d['description'],
            pub_date = d['date'],
        )
        l.save()

if __name__ == '__main__':
    update()
