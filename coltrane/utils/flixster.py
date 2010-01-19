import os
import sys

# Set the directories and django config so it can be run from cron.
current_dir = os.path.abspath(__file__)
projects_dir = os.sep.join(current_dir.split(os.sep)[:-3])
os.environ['PYTHONPATH'] = projects_dir
sys.path.append(projects_dir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# Text and time manipulation
import re
import time
import datetime
from coltrane import utils
from django.utils.encoding import smart_unicode

# Local application
from django.conf import settings
from coltrane.models import Movie

# Logging
import logging
log = logging.getLogger("jellyroll.utils.flixster")

def enabled():
	ok = hasattr(settings, 'FLIXSTER_USER')
	if not ok:
		log.warn('The Flixster provider is not available because the FLIXSTER_USER is undefined.')
	return ok


class FlixsterClient(object):
	"""
	A minimal Flixster client. 
	"""
	
	def __init__(self, username):
		self.username = username
		
	def __getattr__(self):
		return FlixsterClient(self.username)
		
	def __repr__(self):
		return "<FlixsterClient: %s>" % self.username
		
	def __call__(self):
		
		# Fetch the XML via web request
		url = 'http://www.flixster.com/api/v1/users/%s/ratings.rss' % self.username
		xml = utils.getxml(url)

		# Parse the XML down to the item entries
		channel = xml.find('channel')
		items = channel.findall('item')

		# Make a list to stuff all the cleaned data into.
		movies = []

		# Loop through all the entries
		for item in items:
			
			# Dictionary where we'll stuff all the goodies
			movie_dict = {}
			
			# Get the name of the movie
			title = item.find('title').text
			movie_dict['title'] = smart_unicode(title)
			
			# Get the URL to the review
			url = item.find('link').text
			movie_dict['url'] = smart_unicode(url)
			
			# Get the start rating, translate it to a float.
			rating = item.find('rating').text
			movie_dict['rating'] = _prep_rating(rating)
			
			# Get the pubdate
			pub_date = item.find('pubDate').text
			movie_dict['pub_date'] = utils.parsedate(pub_date)
			
			movies.append(movie_dict)
		
		return movies


def _prep_rating(rating_string):
	"""
	Cleans up a rating string from Flixster RSS and translate 
	it into a float so that we can store it in our database.
	
	For example, we want to change '2 1/2 stars' to 2.5 and '3 stars' to 3.0.
	"""
	bits = rating_string.split()
	stars = float(bits[0])
	if len(bits) == 3:
		stars = stars + 0.5
	return stars

def update():
	"""
	When executed, will update the database with the latest Flixster commits.
	"""
	# Init the GithubClient
	flixster = FlixsterClient(settings.FLIXSTER_USER)

	# Fetch the data
	flixster_data = flixster()
	
	# Process the data
	[_handle_commit(i) for i in flixster_data]


def _handle_commit(movie_dict):
	log.debug("Handling movie: %s", movie_dict['title'])
	try:
		Movie.objects.get(url=movie_dict['url'])
		log.debug("Movie already exists.")
	except Movie.DoesNotExist:
		m = Movie(
			title = movie_dict['title'],
			rating = movie_dict['rating'],
			url = movie_dict['url'],
			pub_date = movie_dict['pub_date'],
			)
		m.save()
		log.debug("Adding movie: %s" % m.title)
		
if __name__ == '__main__':
	update()
