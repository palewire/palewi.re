import datetime

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string

from tagging.fields import TagField
from tagging.models import Tag

from django.db import models

from coltrane.managers import LivePostManager, SyncManager

from django.db.models import signals
from coltrane.signals import create_ticker_item, delete_ticker_item


class Ticker(models.Model):
	content_type = models.ForeignKey(ContentType)
	object_id = models.PositiveIntegerField()
	pub_date = models.DateTimeField()
	content_object = generic.GenericForeignKey('content_type', 'object_id')

	class Meta:
		verbose_name_plural = 'Ticker'

	def __unicode__(self):
		return u'%s: %s' % (self.content_type.model_class().__name__, self.content_object)

	def get_rendered_html(self):
		template_name = 'coltrane/ticker_item_%s.html' % (self.content_type.name)
		return render_to_string(template_name, { 'object': self.content_object })


class Slogan(models.Model):
	title = models.CharField(max_length=250, help_text='Maximum 250 characters.')

	class Meta:
		ordering = ['title']
		
	def __unicode__(self):
		return self.title


class Category(models.Model):
	title = models.CharField(max_length=250, help_text='Maximum 250 characters.')
	slug = models.SlugField(unique=True, help_text='Suggested value automatically generated from title. Must be unique.')
	description = models.TextField(null=True, blank=True)
	
	class Meta:
		ordering = ['title']
		verbose_name_plural = 'Categories'
		
	def __unicode__(self):
		return self.title
		
	def get_absolute_url(self):
		return u"/categories/%s/" % self.slug

	def live_post_set(self):
		from coltrane.models import Post
		return self.entry_set.filter(status=Post.LIVE_STATUS)


class Post(models.Model):
	LIVE_STATUS = 1
	DRAFT_STATUS = 2
	HIDDEN_STATUS = 3
	STATUS_CHOICES = (
		(LIVE_STATUS, 'Live'),
		(DRAFT_STATUS, 'Draft'),
		(HIDDEN_STATUS, 'Hidden'),
	)
	
	wordpress_id = models.IntegerField(unique=True, null=True, blank=True, help_text='The junky old wp_posts id from before the migration', editable=False)
	title = models.CharField(max_length=250, help_text='Maximum 250 characters.')
	slug = models.SlugField(max_length=300, unique_for_date='pub_date', help_text='Suggested value automatically generated from title.')
	body = models.TextField()
	pub_date = models.DateTimeField(default=datetime.datetime.now)
	author = models.ForeignKey(User)
	enable_comments = models.BooleanField(default=True)
	status = models.IntegerField(choices=STATUS_CHOICES, default=LIVE_STATUS, help_text="Only entries with 'Live' status will be publicly displayed.")
	categories = models.ManyToManyField(Category)
	tags = TagField(help_text='Separate tags with spaces.', blank=True)
	live = LivePostManager()
	objects = models.Manager()

	class Meta:
		ordering = ['-pub_date']
	
	def __unicode__(self):
		return self.title
				
	def get_absolute_url(self):
		return ('coltrane_post_detail', (), { 'year': self.pub_date.strftime("%Y"),
												'month': self.pub_date.strftime("%m"),
												'day': self.pub_date.strftime("%d"),
												'slug': self.slug })
												
	get_absolute_url = models.permalink(get_absolute_url)
	
	def get_tags(self):
		return Tag.objects.get_for_object(self)


class Shout(models.Model):
	body = models.TextField(max_length=140)
	posted_by = models.ForeignKey(User)
	slug = models.SlugField(unique_for_date='pub_date', help_text='Suggested value automatically generated from title.')
	pub_date = models.DateTimeField(default=datetime.datetime.now)
	enable_comments = models.BooleanField(default=True)
	post_elsewhere = models.BooleanField('Post to Twitter', default=True, help_text='If checked, this link will be posted to both the blog and Twitter.')

	def __unicode__(self):
		return u'%s' % (self.body)

	def sendtwit(self):
		import twitter
		twitter_api=twitter.Api(username=settings.TWITTER_USER, password=settings.TWITTER_PASSWORD)
		twitter_api.PostUpdate(self.body)
		return

	def save(self):
		if not self.id and self.post_elsewhere:
			self.sendtwit()
		super(Shout, self).save()

	def get_absolute_url(self):
		return ('coltrane_shout_detail', (), { 'year': self.pub_date.strftime("%Y"),
												'month': self.pub_date.strftime("%m"),
												'day': self.pub_date.strftime("%d"),
												'slug': self.slug })
	get_absolute_url = models.permalink(get_absolute_url)


class Video(models.Model):
	title = models.CharField(max_length=250)
	url = models.URLField(unique=True)
	posted_by = models.ForeignKey(User)
	pub_date = models.DateTimeField(default=datetime.datetime.now)
	slug = models.SlugField(unique_for_date='pub_date', help_text='Suggested value automatically generated from title.')
	tags = TagField(help_text='Separate tags with spaces.')
	enable_comments = models.BooleanField(default=True)
	via_name = models.CharField('Via', max_length=250, blank=True, help_text='The name of the person whose site you spotted the link on. Optional.')
	via_url = models.URLField('Via URL', blank=True, help_text='The URL of the site where you spotted the link. Optional.')

	class Meta:
		ordering = ['-pub_date']

	def __unicode__(self):
		return self.title

	def get_absolute_url(self):
		return ('coltrane_video_detail', (), { 'year': self.pub_date.strftime("%Y"),
												'month': self.pub_date.strftime("%m"),
												'day': self.pub_date.strftime("%d"),
												'slug': self.slug })
	get_absolute_url = models.permalink(get_absolute_url)


class Photo(models.Model):
	title = models.CharField(max_length=250)
	url = models.URLField(unique=True)
	posted_by = models.ForeignKey(User)
	pub_date = models.DateTimeField(default=datetime.datetime.now)
	slug = models.SlugField(unique_for_date='pub_date', help_text='Suggested value automatically generated from title.')
	tags = TagField(help_text='Separate tags with spaces.')
	enable_comments = models.BooleanField(default=True)
	via_name = models.CharField('Via', max_length=250, blank=True, help_text='The name of the person whose site you spotted the link on. Optional.')
	via_url = models.URLField('Via URL', blank=True, help_text='The URL of the site where you spotted the link. Optional.')

	class Meta:
		ordering = ['-pub_date']

	def __unicode__(self):
		return self.title

	def get_absolute_url(self):
		return ('coltrane_photo_detail', (), { 'year': self.pub_date.strftime("%Y"),
												'month': self.pub_date.strftime("%m"),
												'day': self.pub_date.strftime("%d"),
												'slug': self.slug })
	get_absolute_url = models.permalink(get_absolute_url)


class Track(models.Model):
	"""A track you listened to. The model is based on last.fm."""

	artist_name = models.CharField(max_length=250)
	track_name = models.CharField(max_length=250)
	url = models.URLField(blank=True)
	pub_date = models.DateTimeField(default=datetime.datetime.now)
	track_mbid = models.CharField("MusicBrainz Track ID", max_length=36, blank=True)
	artist_mbid = models.CharField("MusicBrainz Artist ID", max_length=36, blank=True)
	sync = SyncManager()
	objects = models.Manager()

	class Meta:
		ordering = ("-pub_date",)

	def __unicode__(self):
		return u"%s - %s" % (self.artist_name, self.track_name)


class Link(models.Model):
	title = models.CharField(max_length=250)
	description = models.TextField(blank=True, null=True)
	url = models.URLField(unique=True)
	posted_by = models.ForeignKey(User)
	pub_date = models.DateTimeField(default=datetime.datetime.now)
	slug = models.SlugField(unique_for_date='pub_date', help_text='Suggested value automatically generated from title.')
	tags = TagField(help_text='Separate tags with spaces.')
	enable_comments = models.BooleanField(default=True)
	post_elsewhere = models.BooleanField('Post to del.icio.us', default=True, help_text='If checked, this link will be posted to both the blog and del.icio.us.')
	via_name = models.CharField('Via', max_length=250, blank=True, help_text='The name of the person whose site you spotted the link on. Optional.')
	via_url = models.URLField('Via URL', blank=True, help_text='The URL of the site where you spotted the link. Optional.')
	
	class Meta:
		ordering = ['-pub_date']

	def __unicode__(self):
		return self.title
	
	def save(self):
		if not self.id and self.post_elsewhere:
			import pydelicious
			from django.utils.encoding import smart_str
			pydelicious.add(settings.DELICIOUS_USER, settings.DELICIOUS_PASSWORD,
							smart_str(self.url), smart_str(self.title),
							smart_str(self.tags))
		super(Link, self).save()
	
	def get_absolute_url(self):
		return ('coltrane_link_detail', (), { 'year': self.pub_date.strftime("%Y"),
												'month': self.pub_date.strftime("%m"),
												'day': self.pub_date.strftime("%d"),
												'slug': self.slug })
	get_absolute_url = models.permalink(get_absolute_url)

# Signals
for modelname in [Link, Photo, Post, Shout, Track, Video]:
	signals.post_save.connect(create_ticker_item, sender=modelname)
	
for modelname in [Link, Photo, Post, Shout, Track, Video]:
	signals.post_delete.connect(delete_ticker_item, sender=modelname)