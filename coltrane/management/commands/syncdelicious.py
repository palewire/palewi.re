import logging
logger = logging.getLogger(__name__)
from django.conf import settings
from coltrane.utils import delicious
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync Delicious bookmarks'

    def handle(self, *args, **options):
        logger.debug("Syncing Delicious data")
        client = delicious.DeliciousClient(
            settings.DELICIOUS_USER,
            settings.DELICIOUS_PASSWORD
        )
        client.sync()
