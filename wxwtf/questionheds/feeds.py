from django.contrib.syndication.views import Feed
from models import Item


class RecentHeds(Feed):
    title = "Latest questionheds"
    link = "http://twitter.com/questionheds/"
    description = "Is it news?"
    
    def items(self):
        return Item.objects.order_by('-pub_date')[:10]
    
    def item_title(self, item):
        return item
    
    def item_description(self, item):
        return item.description
    
    def item_pubdate(self, item):
        return item.pub_date
