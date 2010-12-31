from django.conf import settings
from coltrane.utils import lastfm
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync Github commits'

    def handle(self, *args, **options):
        print "Syncing Last.fm data"
        client = lastfm.LastFMClient(
            settings.LASTFM_USER,
            settings.LASTFM_TAG_USAGE_THRESHOLD
        )
        client.sync()
