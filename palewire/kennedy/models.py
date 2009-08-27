from django.db import models

GENDER_CHOICES = (
	('female', 'Female'),
	('male', 'Male'),
)

class FirstName(models.Model):
	gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
	name = models.CharField(max_length=50)

	def __unicode__(self):
		return u'%s (%s)' % (self.name, self.get_gender_display())

class NickName(models.Model):
	gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
	name = models.CharField(max_length=50)

	def __unicode__(self):
		return u'%s (%s)' % (self.name, self.get_gender_display())

class LastName(models.Model):
	name = models.CharField(max_length=50)

	def __unicode__(self):
		return self.name