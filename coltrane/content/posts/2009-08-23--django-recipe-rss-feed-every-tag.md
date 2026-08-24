---
title: 'Django recipe: Make an RSS feed for every tag'
slug: django-recipe-rss-feed-every-tag
published_at: '2009-08-23T17:09:49-07:00'
---
<p>This afternoon I made a small update to the site, adding RSS feeds for every tag in the database. So now, if you like, you can subscribe to the latest content about <a href="http://www.palewire.com/feeds/tag/python/">python</a> or <a href="http://www.palewire.com/feeds/tag/music/">music</a> or <a href="http://www.palewire.com/tags/media/">media</a> or <a href="http://www.palewire.com/tags/">anything else I've got</a>. The feeds are found in the hidden autodiscovery tag at the top of the page, so you'll have to use the pulldown in your browser's URL bar to get at them. But they're there.</p>

<p>Thanks to a number of shortcuts in <a href="http://docs.djangoproject.com/en/dev/ref/contrib/syndication/">Django's feed syndication framework</a> and the excellent <a href="http://code.google.com/p/django-tagging/">django-tagging</a>, it's pretty easy to put something like this together. Here's how I did it.</p>

<p>First, in my blog app's feeds.py file:</p>

<pre lang="python">
# Feeds
from django.contrib.syndication.feeds import Feed, FeedDoesNotExist

# Models
from tagging.models import *

# Helpers
from django.core.exceptions import ObjectDoesNotExist


class TagFeed(Feed):
    """
    The most recent content with a particular tag.
    """
    
    def get_object(self, bits):
        """
        Fetch the Tag object.
        """
        if len(bits) != 1:
            raise ObjectDoesNotExist
        return Tag.objects.get(name__exact=bits[0])
        
    def title(self, obj):
        """
        Set the feed title.
        """
        return "%s . tags . palewire" % obj.name.lower()

    def description(self, obj):
        """
        Set the feed description.
        """
        return "the latest tagged %s" % obj.name.lower()

    def link(self, obj):
        """
        Set the feed link.
        """
        if not obj:
            raise FeedDoesNotExist
        return u'/tags/%s/' % obj.name
        
    def items(self, obj):
        """
        Fetch the latest 10 objects with a particular tag, which is passed as the `obj` argument.
        """
        # Pull all the items with that tag.
        taggeditem_list = obj.items.all()
        # Loop through the tagged items and return just the items with a pub_date attribute
        object_list = [i.object for i in taggeditem_list if getattr(i.object, 'pub_date', False)]
        # Now resort them by the pub_date attribute with the newest coming first
        object_list.sort(key=lambda x: x.pub_date, reverse=True)
        # And return the first ten.
        return object_list[:10]
        
    def item_link(self, obj):
        """
        Set the URL for each tagged item, using the url attribute we have on each of our models.
        """
        if not obj:
            raise FeedDoesNotExist
        return obj.url
</pre>

<p>I then added the new TagFeed class to my feed dictionary in the urls/feeds.py file. You can see it at the bottom there.</p>

<pre lang="python">
# urls
from django.conf.urls.defaults import *

# Feeds
from coltrane.feeds import *

# Feed index page
urlpatterns = patterns('django.views.generic',
    (r'^list/$', 'simple.direct_to_template', {'template': 'coltrane/feed_list.html'}),
)

# RSS feeds mapped to URL slugs
feeds = {
    # Bundles
    'the-full-feed': FullFeed,
    'less-noise': LessNoise,
    # Singletons
    'posts': RecentPosts,
    'comments': RecentComments,
    'shouts': RecentShouts,
    'links': RecentLinks,
    'photos': RecentPhotos,
    'tracks': RecentTracks,
    'books': RecentBooks,
    'commits': RecentCommits,
    'tag': TagFeed,
}

# Feed urlpattern
urlpatterns += patterns('',
    url(r'(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}, name='coltrane_feeds'),
)
</pre>

<p>And finally added the URL to the autodiscovery portion of the head in my tag_detail.html template.</p>

<pre lang="html">
{% block extrarss %}
    <link rel="alternate" type="application/rss+xml" title="latest tagged {{ tag }}" href="/feeds/tag/{{ tag }}/"/>
{% endblock %}
</pre>

<p>You can find my blog's entire codebase online <a href="http://github.com/palewire/palewire.com/tree/master">here</a>. And I always appreciate a good criticism. So if you see anything wrong, fire away.</p>