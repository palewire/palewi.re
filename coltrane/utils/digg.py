# Date and text manipulation
import time
from coltrane import utils
from django.utils.encoding import smart_unicode

# Logging
from qiklog import QikLog

# Local application
from coltrane.models import Link


class DiggClient(object):
    """
    A minimal Digg client. 
    """
    logger = QikLog("coltrane.utils.digg")

    def __init__(self, username, api_key, count=10):
        self.username = username
        self.api_key = api_key
        self.count = count
        
    def __getattr__(self):
        return DiggClient(self.username, self.api_key, self.count)
        
    def __repr__(self):
        return "<DiggClient: %s>" % self.username
        
    def get_latest_data(self):
        
        # Get the users most recent diggs
        self.base_url = 'http://services.digg.com/1.0/endpoint?method=user.getDiggs&username=%s&count=%s'
        self.url = self.base_url % (self.username, self.count)
        self.xml = utils.getxml(self.url)
        # Parse out the story_id and datetime
        self.diggs = [(i.get('story'), i.get('date')) for i in self.xml.getchildren()]
        # A list of we'll ultimately pass out
        self.link_list = []
        # Now loop through the diggs
        for story, date in self.diggs:
            # And pull information about the stories
            story_url = 'http://services.digg.com/2.0/story.getInfo?story_ids=%s' % str(story)
            story_json = utils.getjson(story_url)
            story_obj = story_json['stories'][0]
            # A dict to stuff all the good stuff in
            story_dict = {
                # Since the digg_date is expressed in epoch seconds, 
                # we can start like so...
                'date': utils.parsedate(time.ctime(float(date))),
            }
            # Get the link
            story_dict['url'] = smart_unicode(story_obj.get('url'))
            # Get the title
            story_dict['title'] = smart_unicode(story_obj.get('title'))
            story_dict['description'] = smart_unicode(story_obj.get('description'))
            # Get the topic
            story_dict['topic'] = smart_unicode(story_obj.get("topic").get('name'))
            # Pass the dict out to our list
            self.link_list.append(story_dict)
            
        return self.link_list
    
    def sync(self):
        """
        When executed, will collect update your database with the latest diggs.
        """
        [self._handle_digg(d) for d in self.get_latest_data()]
    
    def _handle_digg(self, d):
        """
        Accepts a data dictionary harvest from Digg's API and logs any new ones the database.
        """
        try:
            # Just test the URL in case it's already been logged.
            l = Link.objects.get(url=d['url'])
            # And just quit out silently if it already exists.
            self.logger.log.debug("Digg already exists for %s" % d["title"])
        except Link.DoesNotExist:
            # If it doesn't exist, add it fresh.
            self.logger.log.debug("Adding link to %s" % d["title"])
            l = Link(
                url = d['url'],
                title = d['title'],
                description = d['description'],
                pub_date = d['date'],
                tags = d['topic'],
            )
            l.save()

