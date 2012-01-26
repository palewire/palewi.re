from coltrane import utils
from datetime import datetime
from django.conf import settings
from django.utils import simplejson


class Feedzilla(object):
    """
    A minimal Feedzilla client.
    """
    URL = 'http://api.feedzilla.com/v1/categories/%(cat)s/articles.json?count=%(count)s'
    
    def __repr__(self):
        return "<Feedzilla>"
    
    def fetch(self, cat):
        params = dict(
            count=100,
            cat=cat,
        )
        data = utils.getjson(self.URL % params)
        headline_list = [
            dict(
                title=i['title'].replace("(%s)" % i['source'], "").strip(),
                link=i['url'],
                description=i['summary'],
                pub_date=utils.parsedate(i['publish_date']),
                source=i['source'],
            ) for i in data['articles']
        ]
        headline_list = [i for i in headline_list if len(i['title']) > 1]
        return [i for i in headline_list if i['title'][-1] == '?']
