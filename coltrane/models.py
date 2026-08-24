# Helpers
import datetime

# Models
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _

# Managers
from coltrane.managers import LivePostManager


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
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=LIVE_STATUS,
        help_text=_("Only 'Live' entries will be publicly displayed."),
    )
    repr_image = models.CharField(max_length=1000, blank=True, default="")
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
