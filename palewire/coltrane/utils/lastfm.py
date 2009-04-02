import datetime
import urllib
import logging
import os
import sys
# Set the directories and django config so it can be run from cron.
current_dir = os.path.abspath(__file__)
projects_dir = os.sep.join(current_dir.split(os.sep)[:-3])
os.environ['PYTHONPATH'] = projects_dir
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.append(projects_dir)

from django.conf import settings
from django.db import transaction
from django.utils.encoding import smart_unicode
from httplib2 import HttpLib2Error
from coltrane import utils
from coltrane.models import Track
from django.template.defaultfilters import slugify
 
#
# API URLs
#
 
RECENT_TRACKS_URL = "http://ws.audioscrobbler.com/1.0/user/%s/recenttracks.xml"
TRACK_TAGS_URL = "http://ws.audioscrobbler.com/1.0/track/%s/%s/toptags.xml"
ARTIST_TAGS_URL = "http://ws.audioscrobbler.com/1.0/artist/%s/toptags.xml"
 
#
# Public API
#
 
log = logging.getLogger("coltrane.utils.lastfm")
 
def enabled():
    return hasattr(settings, 'LASTFM_USER')
 
def update():
    last_update_date = Track.sync.get_last_update()
    log.debug("Last update date: %s", last_update_date)
    
    xml = utils.getxml(RECENT_TRACKS_URL % settings.LASTFM_USER)
    for track in xml.getiterator("track"):
        artist = track.find('artist')
        artist_name = smart_unicode(artist.text)
        artist_mbid = artist.get('mbid')
        track_name = smart_unicode(track.find('name').text)
        track_mbid = smart_unicode(track.find('mbid').text)
        url = smart_unicode(track.find('url').text)
        timestamp = datetime.datetime.fromtimestamp(int(track.find('date').get('uts')))
        if timestamp > last_update_date:
            log.debug("Handling track: %r - %r", artist_name, track_name)
            #tags = _tags_for_track(artist_name, track_name)
            tags = None
            _handle_track(artist_name, artist_mbid, track_name, track_mbid, url, timestamp, tags)
 
#
# Private API
#
 
def _tags_for_track(artist_name, track_name):
    """
Get the top tags for a track. Also fetches tags for the artist. Only
includes tracks that break a certain threshold of usage, defined by
settings.LASTFM_TAG_USAGE_THRESHOLD (which defaults to 15).
"""
    
    urls = [
        ARTIST_TAGS_URL % (urllib.quote(artist_name)),
        TRACK_TAGS_URL % (urllib.quote(artist_name), urllib.quote(track_name)),
    ]
    tags = set()
    for url in urls:
        log.debug("Fetching tags from %r", url)
        try:
            xml = utils.getxml(url)
        except HttpLib2Error, e:
            if e.code == 408:
                return ""
            else:
                raise
        for t in xml.getiterator("tag"):
            count = utils.safeint(t.find("count").text)
            if count >= getattr(settings, 'LASTFM_TAG_USAGE_THRESHOLD', 15):
                tags.add(slugify(smart_unicode(t.find("name").text)))
    return " ".join(tags)
 
@transaction.commit_on_success
def _handle_track(artist_name, artist_mbid, track_name, track_mbid, url, timestamp, tags):
    t, created = Track.objects.get_or_create(
        artist_name = artist_name,
        track_name = track_name,
        pub_date = timestamp,
        url = url,
        track_mbid = track_mbid is not None and track_mbid or '',
        artist_mbid = artist_mbid is not None and artist_mbid or '',
    )
    if created == True:
         print u'Logged %s - %s' % (artist_name, track_name)
    else:
         print "Failed to log the track %s - %s" %  (artist_name, track_name)
