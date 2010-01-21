"""
Changes may be attached to any object.
"""

from django.db import models
from django.test import TestCase

class Author(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)

class Article(models.Model):
    author = models.ForeignKey(Author)
    headline = models.CharField(max_length=100)
    url = models.URLField()

    def __str__(self):
        return self.headline

