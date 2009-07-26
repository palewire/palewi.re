import os
import sys
import time
import dateutil.parser
import dateutil.tz
import logging
import urllib

# Set the directories and django config so it can be run from cron.
current_dir = os.path.abspath(__file__)
projects_dir = os.sep.join(current_dir.split(os.sep)[:-3])
os.environ['PYTHONPATH'] = projects_dir
sys.path.append(projects_dir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.conf import settings
from django.db import transaction
from django.utils.encoding import smart_unicode
from coltrane.models import Link
from coltrane import utils

#
# Super-mini Delicious API
#
class DeliciousClient(object):
	"""
	A super-minimal delicious client :)
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
		return utils.getxml(url, username=self.username, password=self.password)

#
# Public API
#

log = logging.getLogger("coltrane.utils.delicious")

def enabled():
	ok = hasattr(settings, 'DELICIOUS_USER') and hasattr(settings, 'DELICIOUS_PASSWORD')
	if not ok:
		log.warn('The Delicious provider is not available because the '
				 'DELICIOUS_USERNAME and/or DELICIOUS_PASSWORD settings are '
				 'undefined.')
	return ok
	
def update():
	delicious = DeliciousClient(settings.DELICIOUS_USER, settings.DELICIOUS_PASSWORD)

	# Check to see if we need an update
	last_update_date = Link.sync.get_last_update()
	last_post_date = utils.parsedate(delicious.posts.update().get("time"))
	if last_post_date <= last_update_date:
		log.info("Skipping update: last update date: %s; last post date: %s", last_update_date, last_post_date)
		return

	for datenode in reversed(list(delicious.posts.dates().getiterator('date'))):
		dt = utils.parsedate(datenode.get("date"))
		if dt > last_update_date:
			_update_bookmarks_from_date(delicious, dt)
				
#
# Private API
#

def _update_bookmarks_from_date(delicious, dt):
	log.debug("Reading bookmarks from %s", dt)
	xml = delicious.posts.get(dt=dt.strftime("%Y-%m-%d"))
	for post in xml.getiterator('post'):
		info = dict((k, smart_unicode(post.get(k))) for k in post.keys())
		log.debug("Handling bookmark of %r", info["href"])
		_handle_bookmark(info)
_update_bookmarks_from_date = transaction.commit_on_success(_update_bookmarks_from_date)

def _handle_bookmark(info):
	l, created = Link.objects.get_or_create(
		url = info['href'],
		title = info['description'],
		description = info.get('extended', ''),
		pub_date = utils.parsedate(info['time']),
		tags = info['tag']
	)
	if created:
		print "Added %s" % l
	if not created:
		l.description = info['description']
		l.extended = info.get('extended', '')
		l.save()
		print u'Logged %s' % l.description

