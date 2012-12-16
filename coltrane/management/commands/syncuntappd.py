import logging
logger = logging.getLogger(__name__)
from django.conf import settings
from coltrane.utils import untappd
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync Untappd updates'

    def handle(self, *args, **options):
        logger.debug("Syncing Untappd data")
        client = untappd.UntappdClient(
            settings.UNTAPPD_CLIENT_ID,
            settings.UNTAPPD_CLIENT_SECRET,
            'palewire'
        )
        client.sync()



