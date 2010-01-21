# Django settings
from django.conf import settings

# Models and fields
from django.db import models
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

# Signals
from django.db.models import signals
from correx.signals import count_changes

# Managers
from correx.managers import ChangeManager

# Text and date manipulation
import datetime
from django.utils.translation import ugettext_lazy as _


class ChangeType(models.Model):
	"""
	The type of change being recorded. 
	
	Seeded with correction, update, addition and deletion by default.
	"""
	name = models.CharField(max_length=20, primary_key=True, help_text=_('The name of the change type'))
	slug = models.SlugField(unique=True, help_text=_('A stripped version of the name for URL strings'))
	description = models.TextField(null=True, blank=True, help_text=_('A description of the change type'))
	change_count = models.IntegerField(default=0, editable=False, help_text=_('The number of changes of this type. Automated.'))

	class Meta:
		db_table = 'django_content_changetype'
		ordering = ['name']
		verbose_name = _('type')

	def __unicode__(self):
		return u'%s (%s)' % (self.name, self.change_count)
		
	def get_absolute_url(self):
		return u'/change-log/type/%s/' % self.slug

	def get_icon_url(self):
		"""
		The path to this type's default icon image.
		"""
		import os
		root = settings.MEDIA_URL
		if not root:
			root = '/media/'
		path = os.path.join(root, 'img')
		return u'%s/%s.gif' % (path, self.slug)
		
	def count_changes(self):
		"""
		Counts the total number of live changes of this type and saves the result to the `change_count` field.
		"""
		count = self.change_set.filter(is_public=True).count()
		self.change_count = count
		self.save()


class Change(models.Model):
	"""
	A change that is optionally related to a site, app, model or object.
	
	``Managers``
		
		``live()``
			The custom manager live() returns only changes where `is_public` is True. 
			
			Example::
	
				Change.objects.live()
	
	"""
	# A list of all the installed apps in a set of paired tuples.
	# I've excluded the django contrib apps and included them as
	# strings to avoid "magic numbers" and so that it won't matter 
	# if you change their order in settings.py
	# Any modules with parent folders are stripped down with the split function.
	installed_apps = [(i.split('.')[-1], i.split('.')[-1]) for i in settings.INSTALLED_APPS if i.find('django')]
	installed_apps.sort()
	APP_CHOICES = installed_apps
	
	# The change
	description    = models.TextField(help_text=_('A description of the change'))
	change_type    = models.ForeignKey(ChangeType, help_text=_('The type of change'), verbose_name=_('Type'))
	pub_date       = models.DateTimeField(default=datetime.datetime.now, verbose_name=_('Publication date'))
	is_public      = models.BooleanField(default=False, help_text=_('Check this box to publish the comment on the live site.'), verbose_name=_('Publish'))

	# Optional connection to the user making the change
	user           = models.ForeignKey(User, blank=True, null=True, related_name="%(class)s_comments", help_text=_('The name of the user responsible for the change. Optional.'))

	# Optional connections to sites, apps, models and objects in the database
	site           = models.ForeignKey(Site, null=True, blank=True, help_text=_('The site being changed. Optional.'))
	content_app    = models.CharField(max_length=200, choices=APP_CHOICES, null=True, blank=True, help_text=_('The application being changed. Optional.'), verbose_name=_('App'))
	content_type   = models.ForeignKey(ContentType, null=True, blank=True, related_name="content_type_set_for_%(class)s", help_text=_('The table or model being changed. Optional.'), verbose_name=_('Model'))
	object_id      = models.PositiveIntegerField(null=True, blank=True, help_text=_('The particular database record being changed. Optional.'))
	content_object = generic.GenericForeignKey(ct_field='content_type', fk_field='object_id')
	
	# Managers
	objects = ChangeManager()
	
	class Meta:
		db_table = 'django_content_changelog'
		ordering = ['-pub_date']
		get_latest_by = "pub_date"
		verbose_name = _('change')

	def __unicode__(self):
		return self.description

	def get_absolute_url(self):
		return u'/change-log/change/%s/' % self.pk

	def get_short_description(self):
		"""
		A shorter version of the description field for use in tight spaces.
		"""
		return u'%s...' % (self.description[:50])
	get_short_description.short_description = _('Description')
	short_description = property(get_short_description)
	
	def get_content_object(self):
		"""
		The object connected to this record by the content_object generic foreign key.
		"""
		from django.core.exceptions import ObjectDoesNotExist
		try:
			return self.content_object
		except ObjectDoesNotExist:
			return None
	get_content_object.short_description = _('Record')


# Rerun the totals for each ChangeType whenever a Change is saved or deleted.
signals.post_save.connect(count_changes, sender=Change)
signals.post_delete.connect(count_changes, sender=Change)
