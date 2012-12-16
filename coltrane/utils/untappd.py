import logging
logger = logging.getLogger(__name__)
from coltrane import utils
from coltrane.models import Beer


class UntappdClient(object):
    """
    A minimal Untappd client. 
    """
    URI = 'http://api.untappd.com/v4/user/checkins/palewire/?client_id=%(client_id)s&client_secret=%(client_secret)s'
    def __init__(self, client_id, client_secret, username):
        self.url = self.URI % dict(
            client_id=client_id,
            client_secret=client_secret,
            username=username
        )
    
    def __getattr__(self):
        return UntappdClient(self.url)
    
    def __repr__(self):
        return "<UntappdClient: %s>" % self.url
    
    def get_latest_data(self):
        self.location_list = []
        self.json = utils.getjson(self.url)
        self.beer_list = []
        for b in self.json['response']['checkins']['items']:
            d = dict(
                title=b['beer']['beer_name'],
                brewery=b['brewery']['brewery_name'],
                pub_date=utils.parsedate(b['created_at']),
                url='https://untappd.com/user/palewire/checkin/%s' % b['checkin_id'],
            )
            self.beer_list.append(d)
        return self.beer_list 
    
    def sync(self):
        """
        When executed, will collect update your database with the latest books.
        """
        [self._handle_beer(d) for d in self.get_latest_data()]
        
    def _handle_beer(self, d):
        """
        Accepts a data dictionary harvest from Foursquare's API and logs 
        any new ones in the database.
        """
        try:
            # Just test the URL in case it's already been logged 
            b = Beer.objects.get(url=d['url'])
            # And just quit out silently if it already exists.
            logger.debug("Beer already exists for %s" % d["title"])
        except Beer.DoesNotExist:
            # If it doesn't exist, add it fresh.
            logger.debug("Adding beer for %s" % d["title"])
            b = Beer(
                url = d['url'],
                title = d['title'],
                brewery = d['brewery'],
                pub_date = d['pub_date'],
            )
            b.save()


