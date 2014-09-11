from django.db import models


class Item(models.Model):
    """
    A news story with a headline that ends in a questionmark?
    """
    title = models.CharField(max_length=500)
    link = models.CharField(max_length=1000)
    description = models.TextField(blank=True)
    pub_date = models.DateTimeField()
    source = models.CharField(max_length=1000)

    class Meta:
        ordering = ("-pub_date",)
        get_latest_by = 'pub_date'

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return self.link
