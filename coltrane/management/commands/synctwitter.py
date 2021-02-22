from django.conf import settings
from coltrane.utils import tweeter
from django.core.management.base import BaseCommand

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync Twitter updates"

    def handle(self, *args, **options):
        logger.debug("Syncing Twitter data")
        client = tweeter.TwitterClient(settings.TWITTER_USER)
        client.sync()
