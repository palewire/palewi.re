# Models
from coltrane.models import Commit

# Text and time
import dateutil.parser
from pprint import pprint
from coltrane import utils

# Logging
import logging
logger = logging.getLogger(__name__)


class GithubClient(object):
    """
    A minimal Github client. 
    """
    def __init__(self, username, page=1):
        self.username = username
        self.page = page
        self.feed_url = 'https://api.github.com/users/%s/events/public?page=%s' % (
            self.username,
            self.page
        )
        self.commit_list = []
    
    def __getattr__(self):
        return GithubClient(self.username)
        
    def __repr__(self):
        return "<GithubClient: %s>" % self.username
        
    def get_latest_data(self):
        self.json = [d for d in utils.getjson(self.feed_url)
            if d['type'] == 'PushEvent']
        for entry in self.json:
            for commit in entry['payload']['commits']:
                # Create a dict to stuff the goodies
                entry_dict = {
                    'pub_date': dateutil.parser.parse(entry['created_at']),
                    'branch': entry['payload']['ref'].split("/")[-1],
                    'repository': entry['repo']['name'],
                    'message': commit['message'],
                    'url': commit['url'],
                }
                # Add the dict to the entry list
                self.commit_list.append(entry_dict)
        # Pass out the commit_list
        return self.commit_list
    
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

