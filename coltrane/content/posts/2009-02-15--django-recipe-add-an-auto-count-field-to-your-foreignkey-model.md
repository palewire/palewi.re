---
title: 'Django recipe: Add an auto-count field to your model'
slug: django-recipe-add-an-auto-count-field-to-your-foreignkey-model
published_at: '2009-02-15T22:30:00-08:00'
---
<p>Nothing fancy here. A common thing I want to do with Django is publish an "object_list" generic view drawn out of a ForeignKey table that includes each object's total number of occurances.</p>

<p>In English: A list with counts. Like this page reporting the occurrence of different ages in our <a href="http://projects.latimes.com/wardead/age/">California's War Dead</a> database.</p>

<p>There are easy enough way to gets this done in your views.py, or with a custom manager. And it's getting increasingly easy thanks <a href="http://code.djangoproject.com/ticket/3566">the aggregates support</a> that's making it's way into Django 1.1. But, just for the hell of it, I thought I'd throw up my simple solution for these situations. It ain't the only way. But I think it's pretty easy.</p>

<p>So, without any further whatnot, here is Ben's approximation of an auto-count field. The code is a simplification of my freshly published pluggable app, <a href="http://code.google.com/p/django-correx/">django-correx</a>, which you can now download from <a href=" 	 http://code.google.com/p/django-correx/">Google Code</a> or <a href="http://github.com/palewire/django-correx/tree/master">github</a>.</p>

<p>First, in your models.py make two models with a foreign key relationship. (I'm going to keep the example very bare bones, simply for the purpose of demonstration. If you want to see my full file, check it out <a href="http://github.com/palewire/django-correx/blob/9978502dbd92ceb82ee8e9242f0d55da83d719dc/correx/models.py">here</a>.)</p>

<pre lang="Python">from django.db import models

class ChangeType(models.Model):
  name = models.CharField(max_length=20)

class Change(models.Model):
  description = models.TextField()
  change_type = models.ForeignKey(ChangeType)
  pub_date = models.DateTimeField()
  is_public = models.BooleanField(default=False)</pre>

<p>Okay. So that's a start. The goal here is to add the auto-count field to ChangeType and have it regularly update itself with the total number of associated changes that have been set for publication.</p>

<p>What I like to do is add a simple IntegerField that can't be futzed with from the admin, and then attach a method that make the join to the parent table and retrieves the current count. Like so:</p>

<pre lang="Python">class ChangeType(models.Model):
  name = models.CharField(max_length=20)
  change_count = models.IntegerField(default=0, editable=False)

  def count_changes(self):
    """
    Counts the total number of live changes of this type and saves the result to the `change_count` field.
    """
    count = self.change_set.filter(is_public=True).count()
    self.change_count = count
    self.save()</pre>

<p>Now all you need to do is regularly schedule the counts. That's where <a href="http://docs.djangoproject.com/en/dev/topics/signals/">Django's cool signal dispatcher</a> comes in. With a small amount of code, you can instruct your project to loop through the ChangeType table and run our new count_changes method every time there's a change to the Change table. And here's how.</p>

<p>First make a new signals.py file in your app directory that looks something like this:</p>

<pre lang="Python">from django.db.models import signals
from django.dispatch import dispatcher

def count_changes(sender, instance, signal, *args, **kwargs):
  """
  Runs through all the change types and adds up their current numbers
  """
  from correx.models import ChangeType
  for change_type in ChangeType.objects.all():
    change_type.count_changes()</pre>

<p>Then roll back to your models.py and rig up the signals to the post-save and post-delete hooks built into the system.</p>

<pre lang="Python">from django.db import models
from django.db.models import signals
from correx.signals import count_changes

class ChangeType(models.Model):
  name = models.CharField(max_length=20)
  change_count = models.IntegerField(default=0, editable=False)

  def count_changes(self):
    """
    Counts the total number of live changes of this type and saves the result to the `change_count` field.
    """
    count = self.change_set.filter(is_public=True).count()
    self.change_count = count
    self.save()

class Change(models.Model):
  description = models.TextField()
  change_type = models.ForeignKey(ChangeType)
  pub_date = models.DateTimeField()
  is_public = models.BooleanField(default=False)

# Rerun the totals for each ChangeType whenever a Change is saved or deleted.
signals.post_save.connect(count_changes, sender=Change)
signals.post_delete.connect(count_changes, sender=Change)</pre>

<p>And that should do it. Go into your admin and add a couple changes and see if it works.</p>

<p>I love to use this sort of setup so that I can stick with a generic view snippet in my urls.py and avoid having to make joins across tables on simple list pages.</p>

<p>I've been cutting and pasting pretty loose here. So let me know if something doesn't add up. Hope this can be useful to somebody. And, per usual, let me know where I screwed up and we'll sort it out. Thanks.</p>