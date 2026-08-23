import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from coltrane.utils import tweeter

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync Twitter updates"

    def handle(self, *args, **options):
        logger.debug("Syncing Twitter data")
        client = tweeter.TwitterClient(settings.TWITTER_USER)
        client.sync()
