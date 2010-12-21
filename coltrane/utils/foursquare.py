from qiklog import QikLog
from coltrane import utils
from coltrane.models import Location
from django.utils.encoding import smart_unicode


class FoursquareClient(object):
    """
    A minimal Foursquare client. 
    """
    logger = QikLog("coltrane.utils.foursquare")
    
    def __init__(self, url):
        self.url = url
    
    def __getattr__(self):
        return FoursquareClient(self.url)
    
    def __repr__(self):
        return "<FoursquareClient: %s>" % self.url
    
    def get_latest_data(self):
        self.location_list = []
        self.xml = utils.getxml(self.url)
        for checkin in self.xml.getiterator("item"):
            title = smart_unicode(checkin.find('title').text)
            description = smart_unicode(checkin.find('description').text)
            url = smart_unicode(checkin.find('link').text)
            date = checkin.find('pubDate').text
            date = utils.parsedate(date)
            d = dict(
                title=title,
                description=description,
                date=date,
                url=url,
            )
            self.location_list.append(d)
        return self.location_list 
    
    def sync(self):
        """
        When executed, will collect update your database with the latest books.
        """
        [self._handle_location(d) for d in self.get_latest_data()]
        
    def _handle_location(self, d):
        """
        Accepts a data dictionary harvest from Foursquare's API and logs 
        any new ones in the database.
        """
        try:
            # Just test the URL in case it's already been logged 
            l = Location.objects.get(title=d['title'], pub_date=d['date'])
            # And just quit out silently if it already exists.
            self.logger.log.debug("Location already exists for %s" % d["title"])
        except Location.DoesNotExist:
            # If it doesn't exist, add it fresh.
            self.logger.log.debug("Adding location for %s" % d["title"])
            l = Location(
                url = d['url'],
                title = d['title'],
                description = d['description'],
                pub_date = d['date'],
            )
            l.save()


