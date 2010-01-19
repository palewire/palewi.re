import os
import sys

# Set the directories and django config so it can be run from cron.
current_dir = os.path.abspath(__file__)
projects_dir = os.sep.join(current_dir.split(os.sep)[:-3])
os.environ['PYTHONPATH'] = projects_dir
sys.path.append(projects_dir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# Django
from django.conf import settings

# Models
from coltrane.models import Link

# Date manipulation
import time
import dateutil.parser
import dateutil.tz

# Helpers
import urllib
import logging
from coltrane import utils
from django.db import transaction
from django.utils.encoding import smart_unicode


class DeliciousClient(object):
	"""
	A super-minimal delicious client.
	"""
	
	lastcall = 0
	
	def __init__(self, username, password, method='v1'):
		self.username, self.password = username, password
		self.method = method
		
	def __getattr__(self, method):
		return DeliciousClient(self.username, self.password, '%s/%s' % (self.method, method))
		
	def __repr__(self):
		return "<DeliciousClient: %s>" % self.method
		
	def __call__(self, **params):
		# Enforce Yahoo's "no calls quicker than every 1 second" rule
		delta = time.time() - DeliciousClient.lastcall
		if delta < 2:
			time.sleep(2 - delta)
		DeliciousClient.lastcall = time.time()
		url = ("https://api.del.icio.us/%s?" % self.method) + urllib.urlencode(params)		  
		xml = utils.getxml(url, username=self.username, password=self.password)
		return xml


log = logging.getLogger("coltrane.utils.delicious")


def enabled():
	"""
	Test whether the proper settings have been configured by the user.
	"""
	ok = hasattr(settings, 'DELICIOUS_USER') and hasattr(settings, 'DELICIOUS_PASSWORD')
	if not ok:
		log.warn('The Delicious provider is not available because the '
				 'DELICIOUS_USERNAME and/or DELICIOUS_PASSWORD settings are '
				 'undefined.')
	return ok

def update():
	"""
	Updates Delicious data and syncs it to the Link model.
	"""
	delicious = DeliciousClient(settings.DELICIOUS_USER, settings.DELICIOUS_PASSWORD)

	# Check to see if we need an update.
	last_update_date = Link.sync.get_last_update()
	for datenode in reversed(list(delicious.posts.dates().getiterator('date'))):
		dt = utils.parsedate(datenode.get("date"))
		# If the date in the record is the same or newer than the date of the last update..
		if dt.date() >= last_update_date.date():
			# ... pass the data along.
			_update_bookmarks_from_date(delicious, dt)
				

def _update_bookmarks_from_date(delicious, dt):
	"""
	Retrieves and processes all posts from the submitted date.
	"""
	log.debug("Reading bookmarks from %s", dt)
	
	# Grab all the posts
	xml = delicious.posts.get(dt=dt.strftime("%Y-%m-%d"))
	
	# Loop through them
	for post in xml.getiterator('post'):
		# Pull out all the attributes into a dictionary.
		info = dict((k, smart_unicode(post.get(k))) for k in post.keys())
		log.debug("Handling bookmark of %r", info["href"])
		
		# Pass the dictionary along.
		_handle_bookmark(info)

_update_bookmarks_from_date = transaction.commit_on_success(_update_bookmarks_from_date)


def _handle_bookmark(info):
	"""
	Accept a data dictionary drawn from the Delicious API and syncs it to the database.
	"""
	try:
		# Just test the URL in case it's already been logged by another bookmarking service like Delicious.
		l = Link.objects.get(url=info['href'])
		# And just quit out silently if it already exists.
		log.debug("Link already exists for %s" % info["description"])
	
	except Link.DoesNotExist:
		# If it doesn't exist, add it fresh.
		log.debug("Adding link to %s" % info["description"])
		
		l = Link(
			url = info['href'],
			title = info['description'],
			description = info.get('extended', ''),
			pub_date = utils.parsedate(str(info['time'])),
			tags = info['tag']
		)
		l.save()

if __name__ == '__main__':
	update()