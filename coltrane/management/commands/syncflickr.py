from django.conf import settings
from coltrane.utils import flickr
import logging
logger = logging.getLogger(__name__)
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync Flickr photos'

    def handle(self, *args, **options):
        logger.debug("Syncing Flickr data")
        client = flickr.FlickrClient(
            settings.FLICKR_API_KEY,
            settings.FLICKR_USER_ID
        )
        client.sync()
