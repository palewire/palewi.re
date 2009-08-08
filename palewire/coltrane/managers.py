# Helpers
import datetime

# Models
from coltrane.models import *


class LivePostManager(models.Manager):
	"""
	Returns all posts set to be published.
	"""
	
	def get_query_set(self):
		return super(LivePostManager, self).get_query_set().filter(status=self.model.LIVE_STATUS)


class LiveCategoryManager(models.Manager):
	"""
	Returns all categories with at least one live post.
	"""

	def get_query_set(self):
		return super(LiveCategoryManager, self).get_query_set().filter(post_count__gt=0)


class LinkDomainManager(models.Manager):
	"""
	Returns an analysis of the domain names found in the Link model.
	
	The result is formed as a list of tuples, with the domain first and count second.
	"""
	
	def rank(self):
		"""
		All domains in the Link model, ranked from greatest to least.
		"""
		from urlparse import urlparse
		
		# Fetch all the domains
		domains = [urlparse(i.url)[1] for i in self.all()]
		
		# Create a dict to stuff the counts
		domain_count = {}
		
		# Loop through all the domains
		for d in domains:
			try:
				# If it exists in the dict, bump it up one
				domain_count[d]['count'] += 1
			except KeyError:
				# If it doesn't exist yet, add it to the dict
				domain_count[d] = {'count': 1, 'font-size': None}
				
		# Sort the results as a list of tuples, from top to bottom
		domain_tuple = domain_count.items()
		domain_tuple.sort(lambda x,y:cmp(x[1], y[1]))
		domain_tuple.reverse()
		
		# Pass out the results
		return domain_tuple



class SyncManager(models.Manager):
	"""
	A set of utilities for working with the Track model.
	"""

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
			
