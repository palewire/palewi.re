# Helpers
import akismet
import datetime
from django.db import models
from django.utils.html import strip_tags
from django.core.mail import mail_managers
from django.utils.encoding import smart_str
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.utils.text import truncate_html_words, truncate_words, get_text_list

# Settings
from django.conf import settings

# Models
from tagging.models import Tag
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.comments.models import Comment
from django.contrib.contenttypes.models import ContentType

# Fields
from tagging.fields import TagField
from django.contrib.contenttypes import generic

# Managers
from coltrane.managers import *

# Signals
from django.db.models import signals
from django.contrib.comments.signals import comment_was_posted
from coltrane.signals import create_ticker_item, delete_ticker_item, category_count


class Ticker(models.Model):
    """
    A tumblelog of the latest content items, pushed automagically by the functions in signals.py.
    """
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    pub_date = models.DateTimeField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    objects = GFKManager()

    class Meta:
        verbose_name_plural = _('Ticker')
        ordering = ('-pub_date',)

    def __unicode__(self):
        return u'%s: %s' % (self.content_type.model_class().__name__, self.content_object)

    def get_rendered_html(self):
        template_name = 'coltrane/ticker_item_%s.html' % (self.content_type.name)
        return render_to_string(template_name, { 'object': self.content_object,
            'STATIC_URL': settings.STATIC_URL })


class Slogan(models.Model):
    """
    The slogans that randomly appear at the top of the blog when the logo is hovered over.
    """
    title = models.CharField(max_length=250, help_text=_('Maximum 250 characters.'))

    class Meta:
        ordering = ['title']
        
    def __unicode__(self):
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
        
    def __unicode__(self):
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
    
    wordpress_id = models.IntegerField(unique=True, null=True, blank=True, help_text=_('The junky old wp_posts id from before the migration'), editable=False)
    title = models.CharField(max_length=250, help_text=_('Maximum 250 characters.'))
    slug = models.SlugField(max_length=300, unique_for_date='pub_date', help_text=_('Suggested value automatically generated from title.'))
    body_markup = models.TextField(help_text=_('The HTML of the post that is edited by the author.'))
    body_html = models.TextField(null=True, blank=True, editable=False, help_text=_('The HTML of the post after it has been run through Pygments.'))
    pub_date = models.DateTimeField(verbose_name=_('publication date'), default=datetime.datetime.now)
    author = models.ForeignKey(User)
    enable_comments = models.BooleanField(default=True)
    status = models.IntegerField(choices=STATUS_CHOICES, default=LIVE_STATUS, help_text=_("Only entries with 'Live' status will be publicly displayed."))
    categories = models.ManyToManyField(Category)
    tags = TagField(help_text=_('Separate tags with spaces.'), blank=True)
    objects = models.Manager()
    live = LivePostManager()

    class Meta:
        ordering = ['-pub_date']
        get_latest_by = 'pub_date'
    
    def __unicode__(self):
        return self.title

    def save(self, force_insert=False, force_update=False):
        from coltrane.utils.pygmenter import pygmenter
        self.body_html = pygmenter(self.body_markup)
        super(Post, self).save()
    
    def get_absolute_url(self):
        return ('coltrane_post_detail', (), { 'year': self.pub_date.strftime("%Y"),
                                                'month': self.pub_date.strftime("%m"),
                                                'day': self.pub_date.strftime("%d"),
                                                'slug': self.slug })
    get_absolute_url = models.permalink(get_absolute_url)
    url = property(get_absolute_url)
    
    def get_absolute_icon(self):
        return u'%sicons/posts.gif' % (settings.STATIC_URL)

    def get_tag_set(self):
        """
        Returns attached tags as a queryset.
        """
        return Tag.objects.get_for_object(self)
    tag_set = property(get_tag_set)

    def get_rendered_html(self):
        template_name = 'coltrane/ticker_item_%s.html' % (self.__class__.__name__.lower())
        return render_to_string(template_name, { 'object': self })


class ThirdPartyBaseModel(models.Model):
    """
    A base model for the data we'll be pulling from third-party sites.
    """
    url = models.URLField(max_length=1000)
    pub_date = models.DateTimeField(default=datetime.datetime.now, verbose_name=_('publication date'))
    tags = TagField(help_text=_('Separate tags with spaces.'), max_length=1000)
    objects = models.Manager()
    sync = SyncManager()
    
    class Meta:
        ordering = ('-pub_date',)
        abstract = True
        get_latest_by = 'pub_date'

    def get_rendered_html(self):
        template_name = 'coltrane/ticker_item_%s.html' % (self.__class__.__name__.lower())
        return render_to_string(template_name, { 'object': self,
            'STATIC_URL': settings.STATIC_URL })

    def get_absolute_icon(self):
        name = u'%ss' % self.__class__.__name__.lower()
        return u'%sicons/%s.gif' % (settings.STATIC_URL, name)

    def get_tag_list(self, last_word='and'):
        return get_text_list(self.tags.split(' '), last_word)
    tag_list = property(get_tag_list)


class Book(ThirdPartyBaseModel):
    """
    Books I've read.
    """
    isbn = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=250)
    authors = models.CharField(max_length=250, blank=True, null=True)

    def __unicode__(self):
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

    def __unicode__(self):
        return self.title


class Commit(ThirdPartyBaseModel):
    """
    Code I've written.
    """
    repository = models.CharField(max_length=100)
    branch = models.CharField(max_length=100)
    message = models.TextField()
    
    def __unicode__(self):
        return u'%s: %s - %s' % (self.repository, self.branch, self.message)
    title = property(__unicode__)

    def get_short_message(self, words=8):
        """
        Trims message to the specified number of words.
        
        Good for use in the admin.
        """
        return truncate_words(strip_tags(self.message), words)
    short_message = property(get_short_message)


class Link(ThirdPartyBaseModel):
    """
    Links to bookmarks I'd like to recommend.
    """
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return self.title


class Location(ThirdPartyBaseModel):
    """
    A place where I announce my presence.
    """
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)

    def __unicode__(self):
        return self.title


class Movie(ThirdPartyBaseModel):
    """
    Links to movies I've seen and rated.
    """
    title = models.CharField(max_length=250, blank=True, null=True)
    rating = models.FloatField(null=True, blank=True, verbose_name='One to five star rating.')

    def __unicode__(self):
        return self.title


class Photo(ThirdPartyBaseModel):
    """
    Links to photos I want to recommend, including my own.
    """
    title = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return self.title


class Shout(ThirdPartyBaseModel):
    """
    Shorter things I blast out.
    """
    message = models.TextField(max_length=140)

    def __unicode__(self):
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

    def __unicode__(self):
        return u"%s - %s" % (self.artist_name, self.track_name)
    title = property(__unicode__)


# Rankings/Clouds
class TopDomain(models.Model):
    """
    One of the top domains in the Link table.

    The list is collected here so we can make a tag cloud with little overhead.
    """
    name = models.CharField(_('name'), max_length=50, unique=True)
    count = models.IntegerField()
    stratum = models.IntegerField(help_text='The font-size stratum to stick \
        this guy in when puffing up the cloud.')
    objects = models.Manager()
    update = TopDomainUpdateManager()

    class Meta:
        ordering = ('-count', 'name')

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.count)


class TopTag(models.Model):
    """
    One of the top tags on the site.

    The list is collected here so we can make a tag cloud with little overhead.
    """
    tag = models.OneToOneField(Tag)
    name = models.CharField(_('name'), max_length=50, unique=True)
    count = models.IntegerField()
    stratum = models.IntegerField(help_text='The font-size stratum to stick \
        this guy in when puffing up the cloud.')
    objects = models.Manager()
    update = TopTagUpdateManager()

    class Meta:
        ordering = ('-count', 'name')

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.count)


# Signals
from correx.models import Change
for modelname in [Link, Photo, Post, Shout, Track, Comment, Book, Commit, Change, Movie, Location]:
    signals.post_save.connect(create_ticker_item, sender=modelname)

for modelname in [Link, Photo, Post, Shout, Track, Comment, Book, Commit, Change, Movie, Location]:
    signals.post_delete.connect(delete_ticker_item, sender=modelname)

signals.post_save.connect(category_count, sender=Post)
signals.post_delete.connect(category_count, sender=Post)

# Comment moderation
def moderate_comment(sender, comment, request, **kwargs):
    print comment
    ak = akismet.Akismet(
        key = settings.AKISMET_API_KEY,
            blog_url = 'http://%s/' % Site.objects.get_current().domain
    )
    
    data = {
        'user_ip': request.META.get('REMOTE_ADDR', ''),
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'referrer': request.META.get('HTTP_REFERRER', ''),
        'comment_type': 'comment',
        'comment_author': smart_str(comment.user_name),
    }
    
    if ak.comment_check(smart_str(comment.comment), data=data, build_data=True):
        comment.is_removed = True
        comment.save()
    
    if not comment.is_removed:
        email_body = "%s"
        mail_managers ("New comment posted", email_body % (comment.get_as_text()))

comment_was_posted.connect(moderate_comment)

