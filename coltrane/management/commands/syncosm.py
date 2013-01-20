import logging
logger = logging.getLogger(__name__)
from django.conf import settings
from coltrane.utils import osm
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync OSM commits'

    def handle(self, *args, **options):
        logger.debug("Syncing OSM data")
        client = osm.OSMClient()
        client.sync()
