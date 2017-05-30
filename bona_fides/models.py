from django.db import models
from adminsortable.models import Sortable


class Award(Sortable):
    """
    An award I have received or been nominated for.
    """
    title = models.CharField(max_length=1000)
    url = models.CharField(max_length=1000, blank=True)

    class Meta(Sortable.Meta):
        pass

    def __unicode__(self):
        return self.title


class Clip(models.Model):
    """
    A story, app or other things I've published.
    """
    title = models.CharField(max_length=1000)
    url = models.CharField(max_length=1000, blank=True)

    def __unicode__(self):
        return self.title


class SocialMediaProfile(Sortable):
    """
    A link to a social media profile I have on another site.
    """
    title = models.CharField(max_length=250)
    url = models.CharField(max_length=1000)

    class Meta(Sortable.Meta):
        pass

    def __unicode__(self):
        return self.title


class Skill(Sortable):
    """
    A technical skill I have and will mention about on my bio page.
    """
    title = models.CharField(max_length=250)

    class Meta(Sortable.Meta):
        pass

    def __unicode__(self):
        return self.title
