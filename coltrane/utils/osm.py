# Models
from coltrane.models import Commit

# Text and time
import dateutil.parser
from pprint import pprint
from coltrane import utils
from django.utils.encoding import smart_unicode

# Logging
import logging
logger = logging.getLogger(__name__)


class OSMClient(object):
    """
    A minimal OpenStreetMap client. 
    """
    feed_url = 'http://www.openstreetmap.org/user/palewire/edits/feed'
        
    def __repr__(self):
        return "<OSMClient>"
        
    def prep_message(self, s):
        s = s.split("-")
        s = "".join(s[1:])
        s = s.strip()
        return s

    def get_latest_data(self):
        self.xml = utils.getxml(self.feed_url)
        commit_list = []
        for link in self.xml.getiterator("{http://www.w3.org/2005/Atom}entry"):
            entry_dict = dict(
                pub_date = utils.parsedate(link.find('{http://www.w3.org/2005/Atom}published').text),
                message = self.prep_message(link.find('{http://www.w3.org/2005/Atom}title').text),
                branch = '',
                repository = 'openstreetmap',
                url = smart_unicode(link.find('{http://www.w3.org/2005/Atom}id').text)
            )
            commit_list.append(entry_dict)
        print commit_list
        return commit_list
    
    def sync(self):
        [self._handle_commit(i) for i in self.get_latest_data()]
    
    def _handle_commit(self, commit_dict):
        try:
            c = Commit.objects.get(url=commit_dict['url'])
            logger.debug("Already have commit %s (%s)." % (
                commit_dict.get("message"), commit_dict.get("pub_date")
            ))
        except Commit.DoesNotExist:
            c = Commit.objects.create(**commit_dict)
            logger.debug("Adding commit %s (%s)." % (
                commit_dict.get("message"),
                commit_dict.get("pub_date"))
            )

