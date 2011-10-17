import logging
logger = logging.getLogger(__name__)
from django.conf import settings
from coltrane.utils import twitter
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync Twitter updates'

    def handle(self, *args, **options):
        logger.debug("Syncing Twitter data")
        client = twitter.TwitterClient(settings.TWITTER_USER)
        client.sync()



