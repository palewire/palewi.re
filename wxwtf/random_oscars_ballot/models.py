from django.db import models


class Category(models.Model):
    order = models.IntegerField()
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ("order",)
        verbose_name_plural = 'categories'

    def __unicode__(self):
        return self.name


class Nominee(models.Model):
    category = models.ForeignKey(Category)
    name = models.CharField(max_length=250)

    def __unicode__(self):
        return self.name
