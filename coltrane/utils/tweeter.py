import datetime
import logging
import dateutil
import re
import twitter
from django.conf import settings
from django.db import transaction
from django.template.defaultfilters import slugify
from django.utils.http import urlquote
from django.utils.encoding import smart_str, smart_text
from coltrane import utils

# Logging
import logging

logger = logging.getLogger(__name__)

# Models
from coltrane.models import Shout

#
# Globals
#

USER_URL = "http://twitter.com/%s"

TWITTER_TRANSFORM_MSG = False
TWITTER_RETWEET_TXT = "Forwarding from %s: "
try:
    TWITTER_TRANSFORM_MSG = settings.TWITTER_TRANSFORM_MSG
    TWITTER_RETWEET_TXT = settings.TWITTER_RETWEET_TXT
except AttributeError:
    pass

#
# The biz
#


class TwitterClient(object):
    """
    A minimal Twitter client.
    """

    def __init__(self, username):
        self.username = username

    def __getattr__(self):
        return TwitterClient(self.username)

    def __repr__(self):
        return "<TwitterClient: %s>" % self.username

    def sync(self):
        last_update_date = Shout.sync.get_last_update()
        logger.debug("Last update date: %s", last_update_date)
        api = twitter.Api(
            consumer_key=settings.TWITTER_CONSUMER_KEY,
            consumer_secret=settings.TWITTER_CONSUMER_SECRET,
            access_token_key=settings.TWITTER_ACCESS_TOKEN_KEY,
            access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
        )
        for status in api.GetUserTimeline(screen_name=settings.TWITTER_USER):
            message_text = smart_text(status.text)
            url = smart_text(
                "https://twitter.com/%s/status/%s" % (settings.TWITTER_USER, status.id)
            )
            # pubDate delivered as UTC
            timestamp = utils.parsedate(status.created_at)
            if not self._status_exists(url):
                self._handle_status(message_text, url, timestamp)

    def _handle_status(self, message_text, url, timestamp):
        message_text, tags = _parse_message(message_text)
        if not self._status_exists(url):
            logger.debug("Saving message: %r", message_text)
            s = Shout.objects.create(
                message=message_text,
                url=url,
                pub_date=timestamp,
            )

    def _status_exists(self, url):
        try:
            Shout.objects.get(url=url)
        except Shout.DoesNotExist:
            return False
        else:
            return True


#
# Tweet transformation
#

if TWITTER_TRANSFORM_MSG:
    USER_LINK_TPL = '<a href="%s" title="%s">%s</a>'
    LINK_LINK_TPL = '<a href="%s" title="%s">%s</a>'
    TAG_RE = re.compile(r"(?P<tag>\#\w+)")
    USER_RE = re.compile(r"(?P<username>@\w+)")
    RT_RE = re.compile(r"RT\s+(?P<username>@\w+)")
    USERNAME_RE = re.compile(r"^%s:" % settings.TWITTER_USER)

    # modified from django.forms.fields.url_re
    URL_RE = re.compile(
        r"https?://"
        r"(?:(?:[A-Z0-9-]+\.)+[A-Z]{2,6}|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/\S+|/?)",
        re.IGNORECASE,
    )

    def _transform_retweet(matchobj):
        if "%s" in TWITTER_RETWEET_TXT:
            return TWITTER_RETWEET_TXT % matchobj.group("username")
        return TWITTER_RETWEET_TXT

    def _transform_user_ref_to_link(matchobj):
        user = matchobj.group("username")[1:]
        link = USER_URL % user
        return USER_LINK_TPL % (link, user, "".join(["@", user]))

    def _parse_message(message_text):
        """
        Parse out some semantics for teh lulz.

        """
        tags = ""

        # remove newlines
        message_text = message_text.replace("\n", "")

        # convert links to HTML
        links = [link for link in URL_RE.findall(message_text)]
        for link in URL_RE.finditer(message_text):
            link_html = LINK_LINK_TPL % (link.group(0), link.group(0), link.group(0))
            message_text = message_text.replace(link.group(0), link_html)

        # remove leading username
        message_text = USERNAME_RE.sub("", message_text)

        # check for RT-type retweet syntax
        message_text = RT_RE.sub(_transform_retweet, message_text)

        # replace @user references with links to their timeline
        message_text = USER_RE.sub(_transform_user_ref_to_link, message_text)

        # generate tags list
        tags = " ".join([tag[1:] for tag in TAG_RE.findall(message_text)])

        return (message_text.strip(), tags)


else:
    _parse_message = lambda msg: (msg, list(), "")
