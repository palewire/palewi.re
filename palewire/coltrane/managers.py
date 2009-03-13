from coltrane.models import *


class LivePostManager(models.Manager):
	

	def get_query_set(self):
		return super(LivePostManager, self).get_query_set().filter(status=self.model.LIVE_STATUS)
		
		
class SyncManager(models.Manager):

	def get_last_update(self, **kwargs):
		"""
		Return the last time a given model's items were updated. Returns the
		epoch if the items were never updated.
		"""
		qs = self
		if kwargs:
			qs = self.filter(**kwargs)
		try:
			return qs.order_by('-pub_date')[0].pub_date
		except IndexError:
			return datetime.datetime.fromtimestamp(0)
