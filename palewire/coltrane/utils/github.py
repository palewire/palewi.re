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
import dateutil.parser
from coltrane import utils
from BeautifulSoup import BeautifulSoup
from django.utils.encoding import smart_unicode

# Local application
from django.conf import settings
from coltrane.models import Commit

# Logging
import logging
log = logging.getLogger("jellyroll.utils.github")

from pprint import pprint

def enabled():
	ok = hasattr(settings, 'GITHUB_USER')
	if not ok:
		log.warn('The Github provider is not available because the GITHUB_USER is undefined.')
	return ok


class GithubClient(object):
	"""
	A minimal Github client. 
	"""
	
	def __init__(self, username):
		self.username = username
		
	def __getattr__(self):
		return GithubClient(self.username)
		
	def __repr__(self):
		return "<GithubClient: %s>" % self.username
		
	def __call__(self):
		
		[i.delete() for i in Commit.objects.all()]
		
		# Fetch the XML via web request
		url = 'http://github.com/%s.atom' % self.username
		xml = utils.getxml(url)
		
		commits = []
		
		GITHUB_TITLE_REGEX = re.compile(r'palewire pushed to (?P<branch>(.*)) at (?P<repository>(.*))')
		
		# Loop through all the entries
		entries = list(xml.getiterator('{http://www.w3.org/2005/Atom}entry'))
		for entry in entries:
			
			# Grab the date
			pub_date = entry.find('{http://www.w3.org/2005/Atom}published').text
			
			# Grab the title
			title = entry.find('{http://www.w3.org/2005/Atom}title').text
			
			# Test it against our regex
			match = GITHUB_TITLE_REGEX.search(title)
			
			# If it doesn't match, it's one of the less important entries
			# like when you start watching somebody's repo.
			if not match:
				# And we can just skip those
				continue
				
			# Grab the HTML with the commits
			html = entry.find('{http://www.w3.org/2005/Atom}content').text
			soup = BeautifulSoup(html)
			commits_html = soup.find('div', attrs={'class': 'commits'}).findAll('li')
			
			# Loop through the one-to-many commits
			for commit_html in commits_html:
				
				# Create a dict to stuff the goodies
				entry_dict = {}
				entry_dict['pub_date'] = dateutil.parser.parse(pub_date)
				
				# Add the matches to our dictionary
				entry_dict['branch'] = smart_unicode(match.group('branch'))
				entry_dict['repository'] = smart_unicode(match.group('repository'))
				
				# Add the others
				entry_dict['url'] = smart_unicode(commit_html.find('a')['href'])
				entry_dict['message'] = smart_unicode(commit_html.find('blockquote').string.strip())
		
				# Add the dict to the entry list
				commits.append(entry_dict)
		
		return commits


def update():
	"""
	When executed, will update the database with the latest Gibhub commits.
	"""
	# Init the GithubClient
	github = GithubClient(settings.GITHUB_USER)

	# Fetch the data
	github_data = github()
	
	# Process the data
	[_handle_commit(i) for i in github_data]


def _handle_commit(commit_dict):
	log.debug("Handling commit from %s", commit_dict['repository'])
	try:
		Commit.objects.get(url=commit_dict['url'])
		log.debug("Commit already exists.")
	except Commit.DoesNotExist:
		c = Commit(
			url = commit_dict['url'],
			pub_date = commit_dict['pub_date'],
			repository = commit_dict['repository'],
			branch = commit_dict['branch'],
			message = commit_dict['message'],
			)
		c.save()
		log.debug("Adding commit.")
		
if __name__ == '__main__':
	update()
		
		
		
	
