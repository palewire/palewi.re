# Feeds
from wxwtf.questionheds.feeds import RecentHeds
from django.contrib.syndication.views import Feed, FeedDoesNotExist

# Models
from coltrane.models import *
from tagging.models import *
from correx.models import Change
from django_comments.models import Comment

# Helpers
from django.shortcuts import get_object_or_404


class TagFeed(Feed):
    """
    The most recent content with a particular tag.
    """

    def get_object(self, request, slug):
        """
        Fetch the Tag object.
        """
        return get_object_or_404(Tag, name=slug)

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


class CategoryFeed(Feed):
    """
    The most recent content with a particular category.
    """

    def get_object(self, request, slug):
        """
        Fetch the Tag object.
        """
        return get_object_or_404(Category, slug=slug)

    def title(self, obj):
        """
        Set the feed title.
        """
        return "%s . category . palewire" % obj.title.lower()

    def description(self, obj):
        """
        Set the feed description.
        """
        return "the latest posts about %s" % obj.title.lower()

    def link(self, obj):
        """
        Set the feed link.
        """
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def items(self, obj):
        """
        Fetch the latest 10 posts in a particular category, which is passed as the `obj` argument.
        """
        object_list = obj.post_set.all().order_by("-pub_date")
        # And return the first ten.
        return object_list[:10]

    def item_link(self, obj):
        """
        Set the URL for each tagged item, using the url attribute we have on each of our models.
        """
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()


class FullFeed(Feed):
    title = "the full feed . palewire"
    link = "http://palewi.re/feeds/the-full-feed/"
    description = "the latest from palewi.re"

    def items(self):
        return Ticker.objects.all().order_by('-pub_date')[:10]

    def item_pubdate(self, item):
        return item.pub_date

    def item_link(self, item):
        try:
            return item.content_object.url
        except AttributeError:
            return item.content_object.get_absolute_url()


class LessNoise(Feed):
    title = "less noise . palewire"
    link = "http://palewi.re/feeds/less-noise/"
    description = "the latest from palewi.re, except for all those tracks"

    def items(self):
        return Ticker.objects.exclude(content_type__name__iexact='Track').order_by('-pub_date')[:10]

    def item_pubdate(self, item):
        return item.pub_date

    def item_link(self, item):
        try:
            return item.content_object.url
        except AttributeError:
            return item.content_object.get_absolute_url()


class RecentPosts(Feed):
    title = "posts . palewire"
    link = "http://palewi.re/feeds/posts/"
    description = "the latest posts at palewi.re"

    def items(self):
        return Post.live.all().order_by('-pub_date')[:10]

    def item_pubdate(self, item):
        return item.pub_date


class RecentBeers(Feed):
    title = "beers . palewire"
    link = "http://palewi.re/feeds/beers/"
    description = "the latest beers at palewi.re"

    def items(self):
        return Beer.objects.all().order_by('-pub_date')[:10]

    def item_link(self, item):
        return item.url

    def item_pubdate(self, item):
        return item.pub_date


class RecentBooks(Feed):
    title = "books . palewire"
    link = "http://palewi.re/feeds/books/"
    description = "the latest books at palewi.re"

    def items(self):
        return Book.objects.all().order_by('-pub_date')[:10]

    def item_link(self, item):
        return item.url

    def item_pubdate(self, item):
        return item.pub_date


class RecentCommits(Feed):
    title = "code commits . palewire"
    link = "http://palewi.re/feeds/commits/"
    description = "the latest code commits at palewi.re"

    def items(self):
        return Commit.objects.all().order_by('-pub_date')[:10]

    def item_link(self, item):
        return item.url

    def item_pubdate(self, item):
        return item.pub_date


class RecentCorrections(Feed):
    title = "corrections . palewire"
    link = "http://palewi.re/feeds/corrections/"
    description = "the latest corrections at palewi.re"
    title_template = 'feeds/change_title.html'
    description_template = 'feeds/change_description.html'

    def items(self):
        return Change.objects.live().order_by('-pub_date')[:10]

    def item_pubdate(self, item):
        return item.pub_date

    def item_link(self, item):
        return u'http://www.palewi.re/corrections/%s/' % item.id


class RecentLinks(Feed):
    title = "links . palewire"
    link = "http://palewi.re/feeds/links/"
    description = "the latest links at palewi.re"

    def items(self):
        return Link.objects.all().order_by('-pub_date')[:10]

    def item_link(self, item):
        return item.url

    def item_pubdate(self, item):
        return item.pub_date


class RecentLocations(Feed):
    title = "locations . palewire"
    link = "http://palewi.re/feeds/locations/"
    description = "the latest locations at palewi.re"

    def items(self):
        return Location.objects.all().order_by('-pub_date')[:10]

    def item_link(self, item):
        return item.url

    def item_pubdate(self, item):
        return item.pub_date


class RecentMovies(Feed):
    title = "movies . palewire"
    link = "http://palewi.re/feeds/movies/"
    description = "the latest movies at palewi.re"

    def items(self):
        return Movie.objects.all().order_by('-pub_date')[:10]

    def item_link(self, item):
        return item.url

    def item_pubdate(self, item):
        return item.pub_date


class RecentPhotos(Feed):
    title = "photos . palewire"
    link = "http://palewi.re/feeds/photos/"
    description = "the latest photos at palewi.re"

    def items(self):
        return Photo.objects.all().order_by('-pub_date')[:10]

    def item_link(self, item):
        return item.url

    def item_pubdate(self, item):
        return item.pub_date


class RecentTracks(Feed):
    title = "tracks . palewire"
    link = "http://palewi.re/feeds/tracks/"
    description = "the latest tracks at palewi.re"

    def items(self):
        return Track.objects.all().order_by('-pub_date')[:10]

    def item_link(self, item):
        return item.url

    def item_pubdate(self, item):
        return item.pub_date


class RecentShouts(Feed):
    title = "shouts . palewire"
    link = "http://palewi.re/feeds/shouts/"
    description = "the latest shouts at palewi.re"

    def items(self):
        return Shout.objects.all().order_by('-pub_date')[:10]

    def item_link(self, item):
        return item.url

    def item_pubdate(self, item):
        return item.pub_date


class RecentComments(Feed):
    title = "comments . palewire"
    link = "http://palewi.re/feeds/comments/"
    description = "the latest comments at palewi.re"

    def items(self):
        return Comment.objects.filter(is_public=True).order_by('-submit_date')[:10]

    def item_pubdate(self, item):
        return item.submit_date
