import logging
logger = logging.getLogger(__name__)
from django.conf import settings
from coltrane.utils import digg
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync Digg votes'

    def handle(self, *args, **options):
        logger.debug("Syncing Digg data")
        client = digg.DiggClient(settings.DIGG_USER)
        client.sync()
