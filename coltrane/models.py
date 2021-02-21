# Helpers
import datetime
from django.db import models
from django.utils.html import strip_tags
from django.core.mail import mail_managers
from django.utils.encoding import smart_str
from django.utils.text import get_text_list
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import truncatewords as truncate_words
from django.template.defaultfilters import truncatewords_html as truncate_html_words

# Settings
from django.conf import settings

# Models
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType

# Fields
from django.contrib.contenttypes import fields as generic

# Managers
from coltrane.managers import *

# Signals
from django.db.models import signals
from coltrane.signals import create_ticker_item, delete_ticker_item, category_count


class Ticker(models.Model):
    """
    A tumblelog of the latest content items, pushed automagically by the functions in signals.py.
    """
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    pub_date = models.DateTimeField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name_plural = _('Ticker')
        ordering = ('-pub_date',)

    def __str__(self):
        return u'%s: %s' % (self.content_type.model_class().__name__, self.content_object)


class Slogan(models.Model):
    """
    The slogans that randomly appear at the top of the blog when the logo is hovered over.
    """
    title = models.CharField(max_length=250, help_text=_('Maximum 250 characters.'))

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class Category(models.Model):
    """
    Topic labels for grouping blog entries.
    """
    title = models.CharField(max_length=250, help_text=_('Maximum 250 characters.'))
    slug = models.SlugField(unique=True, help_text=_('Suggested value automatically generated from title. Must be unique.'))
    description = models.TextField(null=True, blank=True)
    post_count = models.IntegerField(default=0, editable=False)
    objects = models.Manager()
    live = LiveCategoryManager()

    class Meta:
        ordering = ['title']
        verbose_name_plural = _('Categories')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return('coltrane_category_detail', [self.slug])
    get_absolute_url = models.permalink(get_absolute_url)

    def get_absolute_icon(self):
        return u'%sicons/categories.gif' % (settings.STATIC_URL)

    def get_live_post_count(self):
        from coltrane.models import Post
        return Post.live.filter(categories=self).count()


class Post(models.Model):
    """
    Blog posts. For longer stuff I write.

    Supports pygments by placing code in <pre lang="xxx"> tags.
    """
    LIVE_STATUS = 1
    DRAFT_STATUS = 2
    HIDDEN_STATUS = 3
    STATUS_CHOICES = (
        (LIVE_STATUS, 'Live'),
        (DRAFT_STATUS, 'Draft'),
        (HIDDEN_STATUS, 'Hidden'),
    )

    wordpress_id = models.IntegerField(unique=True, null=True, blank=True,
        help_text=_('The junky old wp_posts id from before the migration'),
        editable=False)
    title = models.CharField(max_length=250,
        help_text=_('Maximum 250 characters.'))
    slug = models.SlugField(max_length=300, unique_for_date='pub_date',
        help_text=_('Suggested value automatically generated from title.'))
    body_markup = models.TextField(
        help_text=_('The HTML of the post that is edited by the author.')
    )
    body_html = models.TextField(null=True, blank=True, editable=False,
        help_text=_('The HTML of the post run through Pygments.')
    )
    pub_date = models.DateTimeField(_('publication date'),
        default=datetime.datetime.now)
    author = models.ForeignKey(User)
    enable_comments = models.BooleanField(default=False)
    status = models.IntegerField(choices=STATUS_CHOICES, default=LIVE_STATUS,
        help_text=_("Only 'Live' entries will be publicly displayed."))
    repr_image = models.CharField(max_length=1000, blank=True, default="")
    categories = models.ManyToManyField(Category)
    objects = models.Manager()
    live = LivePostManager()

    class Meta:
        ordering = ['-pub_date']
        get_latest_by = 'pub_date'

    def __str__(self):
        return self.title

    def save(self, force_insert=False, force_update=False):
        from coltrane.utils.pygmenter import pygmenter
        self.body_html = pygmenter(self.body_markup)
        super(Post, self).save()

    def get_absolute_url(self):
        return ('coltrane_post_detail', (), {
            'year': self.pub_date.strftime("%Y"),
            'month': self.pub_date.strftime("%m"),
            'day': self.pub_date.strftime("%d"),
            'slug': self.slug
        })
    get_absolute_url = models.permalink(get_absolute_url)
    url = property(get_absolute_url)

    def get_archive_url(self):
        """
        Overriding the URL to send to Internet Archive so that it has a cachebuster.
        """
        domain = 'http://palewi.re'
        cache_buster = "?timestamp={}".format(datetime.datetime.now().strftime("%s"))
        return domain + self.get_absolute_url() + cache_buster

    def get_publication_status(self):
        """
        Overriding the autoarchiver's indicator of whether or not this post is live.

        My posts are live when the `status` field equals 1. I know. It's dumb.
        """
        return self.status == 1

    def get_absolute_icon(self):
        return u'%sicons/posts.gif' % (settings.STATIC_URL)

    def get_rendered_html(self):
        template_name = 'coltrane/ticker_item_%s.html' % (self.__class__.__name__.lower())
        return render_to_string(template_name, { 'object': self })


class ThirdPartyBaseModel(models.Model):
    """
    A base model for the data we'll be pulling from third-party sites.
    """
    url = models.URLField(max_length=1000)
    pub_date = models.DateTimeField(default=datetime.datetime.now, verbose_name=_('publication date'))
    objects = models.Manager()
    sync = SyncManager()

    class Meta:
        ordering = ('-pub_date',)
        abstract = True
        get_latest_by = 'pub_date'


class Beer(ThirdPartyBaseModel):
    """
    A beer I drank.
    """
    title = models.CharField(max_length=250, blank=True, null=True)
    brewery = models.CharField(max_length=250)

    def __str__(self):
        return self.title


class Book(ThirdPartyBaseModel):
    """
    Books I've read.
    """
    isbn = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=250)
    authors = models.CharField(max_length=250, blank=True, null=True)

    def __str__(self):
        if self.authors:
            return "%s by %s" % (self.title, self.authors)
        else:
            return self.title


class Link(ThirdPartyBaseModel):
    """
    Links to bookmarks I'd like to recommend.
    """
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title


class Commit(ThirdPartyBaseModel):
    """
    Code I've written.
    """
    repository = models.CharField(max_length=100)
    branch = models.CharField(max_length=100, blank=True)
    message = models.TextField()

    def __str__(self):
        if self.branch:
            return u'%s: %s - %s' % (self.repository, self.branch, self.message)
        else:
            return u'%s: %s' % (self.repository, self.message)
    title = property(__str__)

    def get_short_message(self, words=8):
        """
        Trims message to the specified number of words.

        Good for use in the admin.
        """
        return truncate_words(strip_tags(self.message), words)
    short_message = property(get_short_message)


class Location(ThirdPartyBaseModel):
    """
    A place where I announce my presence.
    """
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)

    def __str__(self):
        return self.title


class Movie(ThirdPartyBaseModel):
    """
    Links to movies I've seen and rated.
    """
    title = models.CharField(max_length=250, blank=True, null=True)
    rating = models.FloatField(null=True, blank=True, verbose_name='One to five star rating.')

    def __str__(self):
        return self.title


class Photo(ThirdPartyBaseModel):
    """
    Links to photos I want to recommend, including my own.
    """
    title = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title


class Shout(ThirdPartyBaseModel):
    """
    Shorter things I blast out.
    """
    message = models.TextField(max_length=140)

    def __str__(self):
        return self.message

    def get_short_message(self, words=8):
        """
        Trims message to the specified number of words.

        Good for use in the admin.
        """
        return truncate_words(strip_tags(self.message), words)
    short_message = property(get_short_message)
    title = property(get_short_message)


class Track(ThirdPartyBaseModel):
    """
    Links to tracks I've listened to.
    """
    artist_name = models.CharField(max_length=250)
    track_name = models.CharField(max_length=250)
    track_mbid = models.CharField(verbose_name = _("MusicBrainz Track ID"), max_length=36, blank=True)
    artist_mbid = models.CharField(verbose_name = _("MusicBrainz Artist ID"), max_length=36, blank=True)

    def __str__(self):
        return u"%s - %s" % (self.artist_name, self.track_name)
    title = property(__str__)


# Signals
from correx.models import Change
for modelname in [Link, Photo, Post, Shout, Track, Book, Commit, Change, Movie, Location, Beer]:
    signals.post_save.connect(create_ticker_item, sender=modelname)

for modelname in [Link, Photo, Post, Shout, Track, Book, Commit, Change, Movie, Location, Beer]:
    signals.post_delete.connect(delete_ticker_item, sender=modelname)

signals.post_save.connect(category_count, sender=Post)
signals.post_delete.connect(category_count, sender=Post)
