import logging
logger = logging.getLogger(__name__)
from coltrane import utils
from coltrane.models import Movie
from django.utils.encoding import smart_unicode


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
        
    def get_latest_data(self):
        # Fetch the XML via web request
        self.url = 'http://www.flixster.com/api/v1/users/%s/ratings.rss' % self.username
        self.xml = utils.getxml(self.url)
        # Parse the XML down to the item entries
        self.channel = self.xml.find('channel')
        self.items = self.channel.findall('item')
        # Make a list to stuff all the cleaned data into.
        self.movies = []
        # Loop through all the entries
        for item in self.items:
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
            movie_dict['rating'] = self._prep_rating(rating)
            # Get the pubdate
            pub_date = item.find('pubDate').text
            movie_dict['pub_date'] = utils.parsedate(pub_date)
            # Add it to the list
            self.movies.append(movie_dict)
        return self.movies
    
    def _prep_rating(self, rating_string):
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
    
    def sync(self):
        """
        When executed, will update the database with the latest Flixster commits.
        """
        [self._handle_movie(i) for i in self.get_latest_data()]
    
    def _handle_movie(self, movie_dict):
        try:
            Movie.objects.get(url=movie_dict['url'])
            logger.debug("Movie already exists: %s" % movie_dict['title'])
        except Movie.DoesNotExist:
            m = Movie(
                title = movie_dict['title'],
                rating = movie_dict['rating'],
                url = movie_dict['url'],
                pub_date = movie_dict['pub_date'],
                )
            m.save()
            logger.debug("Adding movie: %s" % m.title)




