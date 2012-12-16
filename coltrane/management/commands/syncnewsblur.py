import logging
logger = logging.getLogger(__name__)
from django.conf import settings
from coltrane.utils import newsblur
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync Delicious bookmarks'

    def handle(self, *args, **options):
        logger.debug("Syncing NewsBlur data")
        client = newsblur.NewsBlurClient()
        client.sync()
