# Models
from coltrane.models import Commit

# Text and time
import re
import dateutil.parser
from coltrane import utils
from BeautifulSoup import BeautifulSoup
from django.utils.encoding import smart_unicode

# Logging
from qiklog import QikLog


class GithubClient(object):
    """
    A minimal Github client. 
    """
    GITHUB_TITLE_REGEX = re.compile(r'palewire pushed to (?P<branch>(.*)) at (?P<repository>(.*))')
    logger = QikLog("jellyroll.utils.github")
    
    def __init__(self, username):
        self.username = username
        self.feed_url = 'http://github.com/%s.atom' % self.username

    def __getattr__(self):
        return GithubClient(self.username)
        
    def __repr__(self):
        return "<GithubClient: %s>" % self.username
        
    def get_latest_data(self):
        self.xml = utils.getxml(self.feed_url)
        self.commit_list = []
        self.entry_list = self.xml.getiterator('{http://www.w3.org/2005/Atom}entry')
        for entry in self.entry_list:
            title = entry.find('{http://www.w3.org/2005/Atom}title').text
            match = self.GITHUB_TITLE_REGEX.search(title)
            # If it doesn't match, it's one of the less important entries
            # like when you start watching somebody's repo.
            if not match:
                # And we can just skip those
                continue
            pub_date = self._extract_entry_pubdate(entry)
            html = entry.find('{http://www.w3.org/2005/Atom}content').text
            soup = BeautifulSoup(html)
            commits_html = soup.find('div', attrs={'class': 'commits'}).findAll('li')
            for commit_html in commits_html:
                # Create a dict to stuff the goodies
                entry_dict = {
                    'pub_date': pub_date,
                    'branch': smart_unicode(match.group('branch')),
                    'repository': smart_unicode(match.group('repository')),
                    'message': self._extract_commit_message(commit_html),
                    'url': self._extract_commit_url(commit_html),
                }
                # Add the dict to the entry list
                self.commit_list.append(entry_dict)
        # Pass out the commit_list
        return self.commit_list
    
    def _extract_entry_pubdate(self, entry):
        text = entry.find('{http://www.w3.org/2005/Atom}published').text
        dt = dateutil.parser.parse(text)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    def _extract_commit_url(self, commit_html):
        href_list = [i['href'] for i in commit_html.findAll('a')]
        commit_url = [i for i in href_list if re.search('commit', i)][0]
        return u'http://github.com%s' % smart_unicode(commit_url)
    
    def _extract_commit_message(self, commit_html):
        s = commit_html.find('blockquote').string.strip()
        return smart_unicode(s)
    
    def sync(self):
        [self._handle_commit(i) for i in self.get_latest_data()]
    
    def _handle_commit(self, commit_dict):
        try:
            c = Commit.objects.get(url=commit_dict['url'])
            self.logger.log.debug("Commit %s already exists." % c)
        except Commit.DoesNotExist:
            c = Commit(
                url = commit_dict['url'],
                pub_date = commit_dict['pub_date'],
                repository = commit_dict['repository'],
                branch = commit_dict['branch'],
                message = commit_dict['message'],
                )
            c.save()
            self.logger.log.debug("Adding commit %s." % c)

