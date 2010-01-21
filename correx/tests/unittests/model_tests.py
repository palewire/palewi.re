from correx.tests import ChangeTestCase
from correx.models import Change, ChangeType

class CorrexModelTests(ChangeTestCase):

	def testSave(self):
		""" 
		Save a set of sample changes.
		"""
		for c in self.createSomeChanges():
			self.failIfEqual(c.pub_date, None)
			c.save()

	def testCount(self):
		"""
		Tests the count_changes() method invoked by signals.py
		"""
		for c in ChangeType.objects.all():
			c.count_changes()
			self.assertEquals(c.change_count, c.change_set.filter(is_public=True).count())