# Feeds
from django.contrib.syndication.feeds import Feed

# Models
from coltrane.models import *
from django.contrib.comments.models import Comment


class FullFeed(Feed):
	title = "the full feed . palewire"
	link = "http://palewire.com/feeds/the-full-feed/"
	description = "the latest from palewire.com"

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
	link = "http://palewire.com/feeds/less-noise/"
	description = "the latest from palewire.com, except for all those tracks"

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
	link = "http://palewire.com/feeds/posts/"
	description = "the latest posts at palewire.com"

	def items(self):
		return Post.live.all().order_by('-pub_date')[:10]

	def item_pubdate(self, item):
		return item.pub_date


class RecentBooks(Feed):
	title = "books . palewire"
	link = "http://palewire.com/feeds/books/"
	description = "the latest shouts at palewire.com"

	def items(self):
		return Book.objects.all().order_by('-pub_date')[:10]

	def item_link(self, item):
		return item.url

	def item_pubdate(self, item):
		return item.pub_date


class RecentShouts(Feed):
	title = "shouts . palewire"
	link = "http://palewire.com/feeds/shouts/"
	description = "the latest shouts at palewire.com"

	def items(self):
		return Shout.objects.all().order_by('-pub_date')[:10]

	def item_link(self, item):
		return item.url

	def item_pubdate(self, item):
		return item.pub_date


class RecentLinks(Feed):
	title = "links . palewire"
	link = "http://palewire.com/feeds/links/"
	description = "the latest links at palewire.com"

	def items(self):
		return Link.objects.all().order_by('-pub_date')[:10]

	def item_link(self, item):
		return item.url

	def item_pubdate(self, item):
		return item.pub_date


class RecentPhotos(Feed):
	title = "photos . palewire"
	link = "http://palewire.com/feeds/photos/"
	description = "the latest photos at palewire.com"

	def items(self):
		return Photo.objects.all().order_by('-pub_date')[:10]

	def item_link(self, item):
		return item.url

	def item_pubdate(self, item):
		return item.pub_date


class RecentTracks(Feed):
	title = "tracks . palewire"
	link = "http://palewire.com/feeds/tracks/"
	description = "the latest tracks at palewire.com"

	def items(self):
		return Track.objects.all().order_by('-pub_date')[:10]

	def item_link(self, item):
		return item.url

	def item_pubdate(self, item):
		return item.pub_date


class RecentComments(Feed):
	title = "comments . palewire"
	link = "http://palewire.com/feeds/comments"
	description = "the latest comments at palewire.com"

	def items(self):
		return Comment.objects.filter(is_public=True).order_by('-submit_date')[:10]
		
	def item_pubdate(self, item):
		return item.submit_date