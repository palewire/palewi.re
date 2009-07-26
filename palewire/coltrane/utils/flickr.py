import datetime
import logging
import urllib
import os
import sys

# Set the directories and django config so it can be run from cron.
current_dir = os.path.abspath(__file__)
projects_dir = os.sep.join(current_dir.split(os.sep)[:-3])
os.environ['PYTHONPATH'] = projects_dir
sys.path.append(projects_dir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.conf import settings
from django.db import transaction
from django.utils.encoding import smart_unicode
from coltrane.models import Photo
from coltrane import utils

try:
	set
except NameError:
	from sets import Set as set		# Python 2.3 fallback

log = logging.getLogger("coltrane.utils.flickr")

#
# Mini FlickrClient API
#

class FlickrError(Exception):
	def __init__(self, code, message):
		self.code, self.message = code, message
	def __str__(self):
		return 'FlickrError %s: %s' % (self.code, self.message)

class FlickrClient(object):
	def __init__(self, api_key, method='flickr'):
		self.api_key = api_key
		self.method = method
		
	def __getattr__(self, method):
		return FlickrClient(self.api_key, '%s.%s' % (self.method, method))
		
	def __repr__(self):
		return "<FlickrClient: %s>" % self.method
		
	def __call__(self, **params):
		params['method'] = self.method
		params['api_key'] = self.api_key
		params['format'] = 'json'
		params['nojsoncallback'] = '1'
		url = "http://flickr.com/services/rest/?" + urllib.urlencode(params)
		json = utils.getjson(url)
		if json.get("stat", "") == "fail":
			raise FlickrError(json["code"], json["message"])
		return json

#
# Public API
#
def enabled():
	ok = (hasattr(settings, "FLICKR_API_KEY") and
		  hasattr(settings, "FLICKR_USER_ID") and
		  hasattr(settings, "FLICKR_USER"))
	if not ok:
	  log.warn('The Flickr provider is not available because the '
			   'FLICKR_API_KEY, FLICKR_USER_ID, and/or FLICKR_USER settings '
			   'are undefined.')
	return ok

def update():
	flickr = FlickrClient(settings.FLICKR_API_KEY)
	
	# Preload the list of licenses
	licenses = licenses = flickr.photos.licenses.getInfo()
	licenses = dict((l["id"], smart_unicode(l["url"])) for l in licenses["licenses"]["license"])
	
	# Handle update by pages until we see photos we've already handled
	last_update_date = Photo.sync.get_last_update()
	page = 1
	while True:
		log.debug("Fetching page %s of photos", page)
		resp = flickr.people.getPublicPhotos(user_id=settings.FLICKR_USER_ID, extras="license,date_taken", per_page="500", page=str(page))
		photos = resp["photos"]
		if page > photos["pages"]:
			log.debug("Ran out of photos; stopping.")
			break
			
		for photodict in photos["photo"]:
			timestamp = utils.parsedate(str(photodict["datetaken"]))
			if timestamp < last_update_date:
				log.debug("Hit an old photo (taken %s; last update was %s); stopping.", timestamp, last_update_date)
				break
			
			photo_id = utils.safeint(photodict["id"])
			license = licenses[photodict["license"]]
			secret = smart_unicode(photodict["secret"])
			server = smart_unicode(photodict["server"])
			_handle_photo(flickr, photo_id, secret, license, timestamp)
			
		page += 1
		
#
# Private API
#

def _handle_photo(flickr, photo_id, secret, license, timestamp):
	info = flickr.photos.getInfo(photo_id=photo_id, secret=secret)["photo"]
	photo_id = str(photo_id)
	taken_by = smart_unicode(info["owner"]["username"])
	url = "http://www.flickr.com/photos/%s/%s/" % (taken_by, photo_id)
	title = smart_unicode(info["title"]["_content"])
	description = smart_unicode(info["description"]["_content"])
	date_uploaded = datetime.datetime.fromtimestamp(utils.safeint(info["dates"]["posted"]))
	tags = _convert_tags(info["tags"])
	
	log.debug("Handling photo: %r (taken %s)" % (title, timestamp))

	try:
		photo = Photo.objects.get(url = url)
		photo.title = title
		photo.description = description
		photo.pub_date = date_uploaded
		photo.tags = tags
		photo.save()
	except Photo.DoesNotExist:
		photo = Photo.objects.create(
			title = title,
			url = url,
			description = description,
			pub_date = date_uploaded,
			tags = tags
		)
		print "Added %s" % photo


_handle_photo = transaction.commit_on_success(_handle_photo)


def _convert_tags(tags):
	return " ".join(set(t["_content"] for t in tags["tag"] if not t["machine_tag"]))