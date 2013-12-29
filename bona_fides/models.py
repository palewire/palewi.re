from django.db import models
from adminsortable.models import Sortable


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
