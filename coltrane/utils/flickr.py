# Models
from coltrane.models import Photo

# Text and misc
import os
import sys
import urllib
import datetime
from coltrane import utils
from django.utils.encoding import smart_unicode

# Logging
import logging
logger = logging.getLogger(__name__)


class FlickrError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message
    def __str__(self):
        return 'FlickrError %s: %s' % (self.code, self.message)


class FlickrClient(object):
    """
    A simple Flickr client.
    """
    def __init__(self, api_key, user_id, method='flickr'):
        self.api_key = api_key
        self.user_id = user_id
        self.method = method
        
    def __getattr__(self, method):
        return FlickrClient(self.api_key, '%s.%s' % (self.method, method))
        
    def __repr__(self):
        return "<FlickrClient: %s>" % self.method
    
    def _get_data(self, **params):
        params['api_key'] = self.api_key
        params['format'] = 'json'
        params['nojsoncallback'] = '1'
        url = "http://flickr.com/services/rest/?" + urllib.urlencode(params)
        json = utils.getjson(url)
        if json.get("stat", "") == "fail":
            raise FlickrError(json["code"], json["message"])
        return json
    
    def get_licenses(self):
        d = self._get_data(method='flickr.photos.licenses.getInfo')
        return dict((l["id"], smart_unicode(l["url"]))
                        for l in d["licenses"]["license"])
    
    def get_photo_page(self, page):
        return self._get_data(
                method='flickr.people.getPublicPhotos',
                user_id=self.user_id,
                extras="license,date_taken",
                per_page="500",
                page=str(page)
            )
    
    def get_photo_info(self, photo_id, secret):
        return self._get_data(
            method='flickr.photos.getInfo', 
            photo_id=photo_id,
            secret=secret
        )
    
    def _convert_tags(self, tags):
        return " ".join(set(t["_content"] for t in tags["tag"] if not t["machine_tag"]))
    
    def sync(self):
        # Preload the list of licenses
        licenses = self.get_licenses()
        # Handle update by pages until we see photos we've already handled
        last_update_date = Photo.sync.get_last_update()
        page = 1
        while True:
            logger.debug("Fetching page %s of photos", page)
            photos = self.get_photo_page(page)["photos"]
            if page > photos["pages"]:
                logger.debug("Ran out of photos; stopping.")
                break
                
            # Loop through all the photos
            for photo in photos["photo"]:
                # Check if the photo is new
                timestamp = utils.parsedate(str(photo["datetaken"]))
                if timestamp < last_update_date:
                    logger.debug(
                        "Hit an old photo (taken %s; last update was %s); \
                        stopping." % (timestamp, last_update_date),
                    )
                    break
                # If it is, get everything ready
                photo_id = utils.safeint(photo["id"])
                license = licenses[photo["license"]]
                secret = smart_unicode(photo["secret"])
                # And pass it to the database
                self._handle_photo(photo_id, secret, license, timestamp)
            
            # Up the page count before closing the loop
            page += 1
    
    def _handle_photo(self, photo_id, secret, license, timestamp):
        # Get all the data ready for the db
        info = self.get_photo_info(photo_id=photo_id, secret=secret)["photo"]
        photo_id = str(photo_id)
        taken_by = smart_unicode(info["owner"]["username"])
        url = "http://www.flickr.com/photos/%s/%s/" % (taken_by, photo_id)
        title = smart_unicode(info["title"]["_content"])
        description = smart_unicode(info["description"]["_content"])
        date_uploaded = datetime.datetime.fromtimestamp(
            utils.safeint(info["dates"]["posted"])
        )
        tags = self._convert_tags(info["tags"])
        logger.debug("Handling photo: %r (taken %s)" % (title, timestamp))
        # Check if it's already in the database
        try:
            # If so, update it.
            photo = Photo.objects.get(url=url)
            photo.title = title
            photo.description = description
            photo.pub_date = date_uploaded
            photo.tags = tags
            photo.save()
        except Photo.DoesNotExist:
            # Otherwise create it from scratch.
            photo = Photo.objects.create(
                title = title,
                url = url,
                description = description,
                pub_date = date_uploaded,
                tags = tags
            )
            logger.debug("Added %s" % photo)


