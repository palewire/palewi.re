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
from qiklog import QikLog


class FlickrError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message
    def __str__(self):
        return 'FlickrError %s: %s' % (self.code, self.message)


class FlickrClient(object):
    """
    A simple Flickr client.
    """
    logger = QikLog("coltrane.utils.flickr")
    
    def __init__(self, api_key, user_id, method='flickr'):
        self.api_key = api_key
        self.user_id = user_id
        self.method = method
        
    def __getattr__(self, method):
        return FlickrClient(self.api_key, '%s.%s' % (self.method, method))
        
    def __repr__(self):
        return "<FlickrClient: %s>" % self.method
        
    def get_data(self, **params):
        # http://flickr.com/services/rest/?api_key=8a3e5e27c7d2b61b26aff9cc011517fe&nojsoncallback=1&method=flickr.photos.licenses.getInfo&format=json
        #params['method'] = params['method']
        params['api_key'] = self.api_key
        params['format'] = 'json'
        params['nojsoncallback'] = '1'
        url = "http://flickr.com/services/rest/?" + urllib.urlencode(params)
        json = utils.getjson(url)
        if json.get("stat", "") == "fail":
            raise FlickrError(json["code"], json["message"])
        return json
    
    def _convert_tags(self, tags):
        return " ".join(set(t["_content"] for t in tags["tag"] if not t["machine_tag"]))
    
    def sync(self):
        # Preload the list of licenses
        licenses = self.get_data(method='flickr.photos.licenses.getInfo')
        licenses = dict((l["id"], smart_unicode(l["url"]))
                        for l in licenses["licenses"]["license"])
        
        # Handle update by pages until we see photos we've already handled
        last_update_date = Photo.sync.get_last_update()
        page = 1
        while True:
            self.logger.log.debug("Fetching page %s of photos", page)
            resp = self.get_data(
                method='flickr.people.getPublicPhotos',
                user_id=self.user_id,
                extras="license,date_taken",
                per_page="500",
                page=str(page)
            )
            photos = resp["photos"]
            
            if page > photos["pages"]:
                self.logger.log.debug("Ran out of photos; stopping.")
                break
                
            for photodict in photos["photo"]:
                timestamp = utils.parsedate(str(photodict["datetaken"]))
                if timestamp < last_update_date:
                    self.logger.log.debug(
                        "Hit an old photo (taken %s; last update was %s); \
                        stopping." % (timestamp, last_update_date),
                    )
                    break
                photo_id = utils.safeint(photodict["id"])
                license = licenses[photodict["license"]]
                secret = smart_unicode(photodict["secret"])
                self._handle_photo(photo_id, secret, license, timestamp)
            page += 1
    
    def _handle_photo(self, photo_id, secret, license, timestamp):
        info = self.get_data(method='flickr.photos.getInfo', photo_id=photo_id, secret=secret)["photo"]
        photo_id = str(photo_id)
        taken_by = smart_unicode(info["owner"]["username"])
        url = "http://www.flickr.com/photos/%s/%s/" % (taken_by, photo_id)
        title = smart_unicode(info["title"]["_content"])
        description = smart_unicode(info["description"]["_content"])
        date_uploaded = datetime.datetime.fromtimestamp(
            utils.safeint(info["dates"]["posted"])
        )
        tags = self._convert_tags(info["tags"])
        
        self.logger.log.debug("Handling photo: %r (taken %s)" % (title, timestamp))
        
        try:
            photo = Photo.objects.get(url=url)
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
            self.logger.log.debug("Added %s" % photo)


