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
from django.utils.encoding import smart_unicode

# Logging
import logging
log = logging.getLogger("coltrane.utils.digg")

# Local application
from django.conf import settings
from coltrane.models import Link


class DiggClient(object):
	"""
	A minimal Digg client. 
	
	If you'd like something more robust, check out Derek van Vliet's "PyDigg":http://neothoughts.com/2007/04/30/pydigg-a-python-toolkit-for-the-digg-api/
	"""
	
	def __init__(self, username, api_key, count):
		self.username = username
		self.api_key = api_key
		self.count = count
		
	def __getattr__(self):
		return DiggClient(self.username, self.api_key, self.count)
		
	def __repr__(self):
		return "<DiggClient: %s>" % self.username
		
	def __call__(self):
		
		# Get the users most recent diggs
		user_url = 'http://services.digg.com/user/%s/diggs/?appkey=%s&count=%s' % (self.username, self.api_key, self.count)
		user_xml = utils.getxml(user_url)
		
		# Parse out the story_id and datetime
		diggs = [(i.get('story'), i.get('date')) for i in user_xml.getchildren()]
		
		# A list of we'll ultimately pass out
		stories = []
		
		# Now loop through the diggs
		for story, date in diggs:
			# And pull information about the stories
			story_url = 'http://services.digg.com/story/%s/?appkey=%s' % (str(story), self.api_key)
			story_xml = utils.getxml(story_url)
			story_obj = story_xml
			
			# A dict to stuff all the good stuff in
			story_dict = {
				# Since the digg_date is expressed in epoch seconds, we can start like so...
				'date': dateutil.parser.parse((time.ctime(float(date)))),
			}
			
			# Loop through the story node
			story_node = story_obj.getiterator('story')
			for ele in story_node:
				# Get the link
				link = smart_unicode(ele.get('link'))
				story_dict['url'] = link
				
				# Get the title
				title_node = ele.find('title')
				story_dict['title'] = smart_unicode(title_node.text)
			
				# Get the description
				description_node = ele.find('description')
				story_dict['description'] = smart_unicode(description_node.text)
				
				# Get the topic
				topic_node = ele.find('topic')
				story_dict['topic'] = smart_unicode(topic_node.get('name'))
			
			# Pass the dict out to our list
			stories.append(story_dict)
			
		return stories


def enabled():
	"""
	Test whether the necessary settings are in place.
	"""
	ok = hasattr(settings, 'DIGG_USER') and hasattr(settings, 'DIGG_API_KEY')
	if not ok:
		log.warn('The Digg provider is not available because the '
				 'DIGG_USER and/or DIGG_API_KEY settings are '
				 'undefined.')
	return ok


def update(diggs_to_fetch=10):
	"""
	When executed, will collect update your database with the latest diggs.
	"""
	# Init the DiggClient
	digg = DiggClient(settings.DIGG_USER, settings.DIGG_API_KEY, diggs_to_fetch)
	
	# Retrieve the data
	digg_data = digg()

	# Now loop through the data and add the new ones.
	[_handle_digg(digg_dict) for digg_dict in digg_data]
		
		
def _handle_digg(digg_dict):
	"""
	Accepts a data dictionary harvest from Digg's API and logs any new ones the database.
	"""
	try:
		# Just test the URL in case it's already been logged by another bookmarking service like Delicious.
		l = Link.objects.get(url=digg_dict['url'])
		# And just quit out silently if it already exists.
		log.debug("Digg already exists for %s" % digg_dict["title"])
	
	except Link.DoesNotExist:
		# If it doesn't exist, add it fresh.
		log.debug("Adding link to %s" % digg_dict["title"])
		
		l = Link(
			url = digg_dict['url'],
			title = digg_dict['title'],
			description = digg_dict['description'],
			pub_date = digg_dict['date'],
			tags = digg_dict['topic'],
		)
		l.save()

if __name__ == '__main__':
	update()
