# Date and text manipulation
import time
import datetime
import dateutil.parser
from coltrane import utils
from django.utils.text import get_text_list
from django.utils.encoding import smart_unicode

# Logging
from qiklog import QikLog

# Models
from coltrane.models import Book


class ReadernautClient(object):
    """
    A minimal Readernaut client. 
    """
    logger = QikLog("coltrane.utils.readernaut")
    
    def __init__(self, username):
        self.username = username
        
    def __getattr__(self):
        return ReadernautClient(self.username)
        
    def __repr__(self):
        return "<ReadernautClient: %s>" % self.username
        
    def get_latest_data(self):
        # Fetch the XML via web request
        url = 'http://readernaut.com/api/v1/xml/%s/books/' % self.username
        xml = utils.getxml(url)
        
        books = []
        
        for book in xml.getchildren():
            
            # Dictionary where we'll stuff all the goodies
            book_dict = {}
            
            # Get the date
            date = book.find('created').text
            book_dict['date'] = dateutil.parser.parse(date)
            
            # Step down the XML
            edition = book.find('book_edition')
            
            # Get the title
            title = edition.find('title').text
            book_dict['title'] = smart_unicode(title)
        
            # Get the ISBN
            isbn = edition.find('isbn').text
            book_dict['isbn'] = smart_unicode(isbn)
            
            # Get the authors as a text list
            authors = []
            for author in edition.getiterator('authors'):
                name = getattr(author.find('author'), 'text', None)
                if name:
                    authors.append(smart_unicode(name))
            book_dict['authors'] = get_text_list(authors, 'and')
            
            # Get the link
            url = edition.find('permalink').text
            book_dict['url'] = smart_unicode(url)
            
            books.append(book_dict)
            
        return books
    
    def sync(self):
        """
        When executed, will collect update your database with the latest books.
        """
        [self._handle_book(book_dict) for book_dict in self.get_latest_data()]
    
    def _handle_book(self, book_dict):
        """
        Accepts a data dictionary harvest from Readernaut's API and logs any new ones the database.
        """
        try:
            # Just test the URL in case it's already been logged by another bookmarking service like Delicious.
            b = Book.objects.get(isbn=book_dict['isbn'])
            # And just quit out silently if it already exists.
            self.logger.log.debug("Book already exists for %s" % book_dict["title"])
        except Book.DoesNotExist:
            # If it doesn't exist, add it fresh.
            self.logger.log.debug("Adding book to %s" % book_dict["title"])
            b = Book(
                url = book_dict['url'],
                title = book_dict['title'],
                authors = book_dict['authors'],
                pub_date = book_dict['date'],
                isbn = book_dict['isbn'],
            )
            b.save()

