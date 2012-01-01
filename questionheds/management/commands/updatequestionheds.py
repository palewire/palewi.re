import logging
logger = logging.getLogger(__name__)
from django.conf import settings
from questionheds.fetch import Feedzilla
from questionheds.models import Item
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync Questionheds from Feedzilla'
    
    def handle(self, *args, **options):
        for cat in [26, 1314, 13, 21, 22, 5, 6, 25]:
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
