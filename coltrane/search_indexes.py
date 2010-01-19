import datetime
from haystack import indexes
from haystack import site
from coltrane.models import *


class PostIndex(indexes.SearchIndex):
	text = indexes.CharField(document=True, use_template=True)
	author = indexes.CharField(model_attr='author')
	pub_date = indexes.DateTimeField(model_attr='pub_date')

	def get_query_set(self):
		return Post.live.all()

site.register(Post, PostIndex)

# THIRD-PARTY DATA MODELS

class BookIndex(indexes.SearchIndex):
	text = indexes.CharField(document=True, use_template=True)
	pub_date = indexes.DateTimeField(model_attr='pub_date')

site.register(Book, BookIndex)


class CommitIndex(indexes.SearchIndex):
	text = indexes.CharField(document=True, use_template=True)
	pub_date = indexes.DateTimeField(model_attr='pub_date')

site.register(Commit, CommitIndex)


class LinkIndex(indexes.SearchIndex):
	text = indexes.CharField(document=True, use_template=True)
	pub_date = indexes.DateTimeField(model_attr='pub_date')

site.register(Link, LinkIndex)


class PhotoIndex(indexes.SearchIndex):
	text = indexes.CharField(document=True, use_template=True)
	pub_date = indexes.DateTimeField(model_attr='pub_date')

site.register(Photo, PhotoIndex)


class ShoutIndex(indexes.SearchIndex):
	text = indexes.CharField(document=True, use_template=True)
	pub_date = indexes.DateTimeField(model_attr='pub_date')

site.register(Shout, ShoutIndex)


class TrackIndex(indexes.SearchIndex):
	text = indexes.CharField(document=True, use_template=True)
	pub_date = indexes.DateTimeField(model_attr='pub_date')

site.register(Track, TrackIndex)
