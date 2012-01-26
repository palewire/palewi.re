import logging
logger = logging.getLogger(__name__)
from django.conf import settings
from wxwtf.questionheds.models import Item
from wxwtf.questionheds.fetch import Feedzilla
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync Questionheds from Feedzilla'
    CATEGORIES = {
        'Top news': 26,
        'Sports': 1314,
        'Art': 13,
        'Blogs': 21,
        'Business': 22,
        'Celebrities': 5,
        'Entertainment': 6,
        'Fun stuff': 25,
        'Health': 11,
        'Internet': 28,
        'Law': 591,
        'Music': 29,
        'Lifestyle': 2,
        'Politics': 3,
        'Music': 29,
        'Programming': 16,
    }

    def handle(self, *args, **options):
        for cat in self.CATEGORIES.values():
            hed_list = Feedzilla().fetch(cat=cat)
            for item in hed_list:
                hits = Item.objects.filter(link=item['link']).count()
                if not hits:
                    logger.debug("Adding %s" % item['title'])
                    obj = Item.objects.create(
                        title=item['title'],
                        link=item['link'],
                        description=item['description'],
                        pub_date=item['pub_date'],
                        source=item['source']
                    )
