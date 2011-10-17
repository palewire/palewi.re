import logging
logger = logging.getLogger(__name__)
from django.conf import settings
from coltrane.utils import foursquare
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync Foursquare checkins'

    def handle(self, *args, **options):
        logger.debug("Syncing Foursquare data")
        client = foursquare.FoursquareClient(settings.FOURSQUARE_RSS)
        client.sync()
