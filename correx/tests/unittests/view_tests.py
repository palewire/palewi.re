from django.utils import simplejson
from django.test.client import Client

from correx.tests import ChangeTestCase
from correx.models import Change, ChangeType

from django.db.models import get_model
from django.contrib.contenttypes.models import ContentType


class CorrexViewTests(ChangeTestCase):
	
	def setUp(self):
		"""
		Setting up the test client for reuse throughout.
		"""
		self.client = Client()
		self.app_list = [i[0] for i in Change().APP_CHOICES]

	def testFilterContentTypesByApp(self):
		"""
		Test the admin jQuery's request for the list of models 
		associated with a particular application.
		"""
		url = '/correx/admin/filter/contenttype/'
		
		for app in self.app_list:
			# Issue a GET request.
			response = self.client.get(url, {'app_label': app})
			
			# Check that the response is 200 OK.
			self.failUnlessEqual(response.status_code, 200)
			
			# Load JSON
			json = simplejson.loads(response.content)
			
			# Test to make sure it's a list
			self.failUnlessEqual(type(json), type([]))
			
			# Split the model names from the json
			model_names = [i.values()[0] for i in json if i.values()[0] != '---------']
			
			# Run through the list and make sure each is a legit model
			for model in model_names:
			
				# If it equals null it means the model couldn't be found
				self.failIfEqual(get_model(app, model), None)
