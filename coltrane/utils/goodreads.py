# Date and text manipulation
import time
import datetime
import dateutil.parser
from coltrane import utils
from django.utils.text import get_text_list
from django.utils.encoding import smart_unicode

# Logging
import logging
logger = logging.getLogger(__name__)

# Models
from coltrane.models import Book


class GoodReadsClient(object):
    """
    A minimal GoodReads client. 
    """
    def __init__(self, user_id, api_key):
        self.user_id = user_id
        self.api_key = api_key

    def __repr__(self):
        return "<GoodReadsClient: %s>" % self.user_id

    def get_latest_data(self):
        # Fetch the XML via web request
        url = 'https://www.goodreads.com/review/list_rss/%s?key=%s&shelf=read' % (
            self.user_id,
            self.api_key
        )
        xml = utils.getxml(url)
        
        books = []
        
        for book in xml.getiterator("item"):

            # Dictionary where we'll stuff all the goodies
            book_dict = {}

            # Get the date
            date = book.find('pubDate').text
            book_dict['date'] = dateutil.parser.parse(date)

            # Get the title
            title = book.find('title').text
            book_dict['title'] = smart_unicode(title)

            # Get the ISBN
            isbn = book.find('isbn').text
            # If no ISBN, substitute the GoodReads id
            if not isbn:
                isbn = 'goodreads:%s' % book.find('book_id').text
            book_dict['isbn'] = smart_unicode(isbn)

            # Get the authors
            author = book.find('author_name').text
            book_dict['authors'] = smart_unicode(author)

            # Get the link
            url = book.find('guid').text
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
            logger.debug("Book already exists for %s" % book_dict["title"])
        except Book.DoesNotExist:
            # If it doesn't exist, add it fresh.
            logger.debug("Adding book to %s" % book_dict["title"])
            b = Book(
                url = book_dict['url'],
                title = book_dict['title'],
                authors = book_dict['authors'],
                pub_date = book_dict['date'],
                isbn = book_dict['isbn'],
            )
            b.save()

