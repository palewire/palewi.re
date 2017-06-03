from django.db import models


class ChangeManager(models.Manager):

	def live(self):
		"""
		All changes set for publication.
		"""
		return self.get_queryset().filter(is_public=True)
