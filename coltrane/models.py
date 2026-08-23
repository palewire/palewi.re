# Helpers
import datetime

# Settings
from django.conf import settings

# Models
from django.contrib.auth.models import User
from django.db import models

# Signals
from django.db.models import signals
from django.urls import reverse
from django.utils.translation import gettext as _

# Managers
from coltrane.managers import LiveCategoryManager, LivePostManager
from coltrane.signals import category_count


class Category(models.Model):
    """
    Topic labels for grouping blog entries.
    """

    title = models.CharField(max_length=250, help_text=_("Maximum 250 characters."))
    slug = models.SlugField(
        unique=True,
        help_text=_("Suggested value automatically generated from title. Must be unique."),
    )
    description = models.TextField(null=True, blank=True)
    post_count = models.IntegerField(default=0, editable=False)
    objects = models.Manager()
    live = LiveCategoryManager()

    class Meta:
        ordering = ["title"]
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return ("coltrane_category_detail", [self.slug])

    def get_absolute_icon(self):
        return "%sicons/categories.gif" % (settings.STATIC_URL)

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
        (LIVE_STATUS, "Live"),
        (DRAFT_STATUS, "Draft"),
        (HIDDEN_STATUS, "Hidden"),
    )

    wordpress_id = models.IntegerField(
        unique=True,
        null=True,
        blank=True,
        help_text=_("The junky old wp_posts id from before the migration"),
        editable=False,
    )
    title = models.CharField(max_length=250, help_text=_("Maximum 250 characters."))
    slug = models.SlugField(
        max_length=300,
        unique_for_date="pub_date",
        help_text=_("Suggested value automatically generated from title."),
    )
    body_markup = models.TextField(help_text=_("The HTML of the post that is edited by the author."))
    body_html = models.TextField(
        null=True,
        blank=True,
        editable=False,
        help_text=_("The HTML of the post run through Pygments."),
    )
    pub_date = models.DateTimeField(_("publication date"), default=datetime.datetime.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    enable_comments = models.BooleanField(default=False)
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=LIVE_STATUS,
        help_text=_("Only 'Live' entries will be publicly displayed."),
    )
    repr_image = models.CharField(max_length=1000, blank=True, default="")
    categories = models.ManyToManyField(Category)
    objects = models.Manager()
    live = LivePostManager()

    class Meta:
        ordering = ["-pub_date"]
        get_latest_by = "pub_date"

    def __str__(self):
        return self.title

    def save(self, force_insert=False, force_update=False, **kwargs):
        from coltrane.utils.pygmenter import pygmenter

        self.body_html = pygmenter(self.body_markup)
        super().save(force_insert=force_insert, force_update=force_update, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "coltrane_post_detail",
            args=(),
            kwargs={
                "year": self.pub_date.strftime("%Y"),
                "month": self.pub_date.strftime("%m"),
                "day": self.pub_date.strftime("%d"),
                "slug": self.slug,
            },
        )

    url = property(get_absolute_url)

    def get_archive_url(self):
        """
        Overriding the URL to send to Internet Archive so that it has a cachebuster.
        """
        domain = "http://palewi.re"
        cache_buster = "?timestamp={}".format(datetime.datetime.now().strftime("%s"))
        return domain + self.get_absolute_url() + cache_buster

    def get_publication_status(self):
        """
        Overriding the autoarchiver's indicator of whether or not this post is live.

        My posts are live when the `status` field equals 1. I know. It's dumb.
        """
        return self.status == 1

    def get_absolute_icon(self):
        return "%sicons/posts.gif" % (settings.STATIC_URL)


# Signals
signals.post_save.connect(category_count, sender=Post)
signals.post_delete.connect(category_count, sender=Post)
