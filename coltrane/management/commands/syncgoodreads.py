import logging
logger = logging.getLogger(__name__)
from django.conf import settings
from coltrane.utils import goodreads
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync GoodReads ratings'

    def handle(self, *args, **options):
        logger.debug("Syncing GoodReads data")
        client = goodreads.GoodReadsClient(
            settings.GOODREADS_USER_ID,
            settings.GOODREADS_API_KEY
        )
        client.sync()
