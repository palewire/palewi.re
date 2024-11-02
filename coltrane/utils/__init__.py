# http
import requests
from requests.auth import HTTPBasicAuth

# Date manipulation
import pytz
import time
import datetime
import dateutil.parser
import dateutil.tz

# Serialization
import json

# Text manipulation
from django.utils.encoding import force_str as force_text

# Django
from django.conf import settings

DEFAULT_HTTP_HEADERS = {"User-Agent": "palewi.re ticker"}

#
# URL fetching sugar
#


def getjson(url, **kwargs):
    """
    Fetch and parse some JSON. Returns the deserialized JSON.
    """
    data = fetch_resource(url, **kwargs)
    return json.loads(data)


def fetch_resource(url, username=None, password=None, headers=None):
    """
    Fetch an URL. Return the content.
    """
    # Empty config dict we'll add to.
    kwargs = {}

    # Add any credentials
    if username or password:
        kwargs.update({"auth": HTTPBasicAuth(username, password)})

    # Set custom headers
    if headers:
        kwargs.update({"headers": headers})
    else:
        kwargs.update({"headers": DEFAULT_HTTP_HEADERS.copy()})

    # Make the request
    return requests.get(url, **kwargs).content


#
# Date handling utils
#


def parsedate(s):
    """
    Convert a string into a local, naive datetime object.
    """
    dt = dateutil.parser.parse(s)
    if dt.tzinfo:
        dt = dt.astimezone(dateutil.tz.tzlocal()).replace(tzinfo=None)
    return dt


def safeint(s):
    """
    Always returns an int. Returns 0 on failure.
    """
    try:
        return int(force_text(s))
    except (ValueError, TypeError):
        return 0


#
# Timezone adjustment
#

UTC = pytz.timezone("UTC")
LOCAL = pytz.timezone(settings.TIME_ZONE)


def utc_to_local_datetime(dt):
    """
    Map datetime as UTC object to it's localtime counterpart.
    """
    return dt.astimezone(LOCAL)


def utc_to_local_timestamp(ts, orig_tz=UTC):
    """
    Convert a timestamp object into a tz-aware datetime object.
    """
    timestamp = datetime.datetime.fromtimestamp(ts, tz=orig_tz)
    return timestamp.astimezone(LOCAL)


def utc_to_local_timestruct(ts, orig_tz=UTC):
    """
    Convert a timestruct object into a tz-aware datetime object.
    """
    return utc_to_local_timestamp(time.mktime(ts), orig_tz)
