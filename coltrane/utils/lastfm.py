# Helpers
import urllib
import datetime
from coltrane import utils
from httplib2 import HttpLib2Error
from django.utils.functional import memoize

# Text
from django.utils.http import urlquote
from django.utils.encoding import smart_unicode
from django.template.defaultfilters import slugify

# Logging
from qiklog import QikLog

# Models
from tagging.models import Tag
from coltrane.models import Track

#
# API URLs
#
 
RECENT_TRACKS_URL = "http://ws.audioscrobbler.com/1.0/user/%s/recenttracks.xml"
TRACK_TAGS_URL = "http://ws.audioscrobbler.com/1.0/track/%s/%s/toptags.xml"
ARTIST_TAGS_URL = "http://ws.audioscrobbler.com/1.0/artist/%s/toptags.xml"


class LastFMClient(object):
    """
    A minimal Last FM client. 
    """
    logger = QikLog("coltrane.utils.lastfm")
    
    def __init__(self, username, tag_usage_threshold=15):
        self.username = username
        self.tag_usage_threshold = tag_usage_threshold
    
    def __getattr__(self):
        return FoursquareClient(self.url)
    
    def __repr__(self):
        return "<FoursquareClient: %s>" % self.url
    
    def sync(self):
        last_update_date = Track.sync.get_last_update()
        xml = utils.getxml(RECENT_TRACKS_URL % self.username)
        for track in xml.getiterator("track"):
            artist = track.find('artist')
            artist_name = smart_unicode(artist.text)
            artist_mbid = artist.get('mbid')
            track_name = smart_unicode(track.find('name').text)
            track_mbid = smart_unicode(track.find('mbid').text)
            url = smart_unicode(track.find('url').text)
            timestamp = datetime.datetime.fromtimestamp(int(track.find('date').get('uts')))
            if timestamp > last_update_date:
                tags = self._tags_for_track(artist_name, track_name)
                self._handle_track(artist_name, artist_mbid, track_name, track_mbid, url, timestamp, tags)
    
    def _tags_for_track(self, artist_name, track_name):
        """
        Get the top tags for a track. Also fetches tags for the artist. Only
        includes tracks that break a certain threshold of usage, defined by
        settings.LASTFM_TAG_USAGE_THRESHOLD (which defaults to 15).
        """
        urls = [
            ARTIST_TAGS_URL % (urlquote(artist_name)),
            TRACK_TAGS_URL % (urlquote(artist_name), urlquote(track_name)),
        ]
        tags = set()
        for url in urls:
            tags.update(self._tags_for_url(url))
        return tags
        
    def _tags_for_url(self, url):
        tags = set()
        try:
            xml = utils.getxml(url)
        except HttpLib2Error, e:
            if e.code == 408:
                return ""
            else:
                raise
        except SyntaxError:
            return ""
        for t in xml.getiterator("tag"):
            count = utils.safeint(t.find("count").text)
            if count >= self.tag_usage_threshold:
                tag = slugify(smart_unicode(t.find("name").text))
                tags.add(tag[:50])
        return tags

    # Memoize tags to avoid unnecessary API calls.
    _tag_cache = {}
    _tags_for_url = memoize(_tags_for_url, _tag_cache, 1)

    def _handle_track(self, artist_name, artist_mbid, track_name, track_mbid,
        url, timestamp, tags):
        t, created = Track.objects.get_or_create(
            artist_name = artist_name,
            track_name = track_name,
            pub_date = timestamp,
            url = url,
            track_mbid = track_mbid is not None and track_mbid or '',
            artist_mbid = artist_mbid is not None and artist_mbid or '',
            tags = " ".join(tags)
        )
        t.save()
        if created == True:
             self.logger.log.debug(u'Logged %s - %s' % (artist_name, track_name))
        else:
             self.logger.log.debug("Failed to log the track %s - %s" %    (artist_name, track_name))


def get_back_tags():
    """
    Loops through old tracks and fetchs their tags. 
    """
    tracks = Track.objects.all()
    for t in tracks:
        tags = _tags_for_track(t.artist_name, t.track_name)
        t.tags = " ".join(tags)
        t.save()
        print t

