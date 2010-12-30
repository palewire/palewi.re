from django.conf import settings
from coltrane.utils import flickr
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync Flickr photos'

    def handle(self, *args, **options):
        print "Syncing Flickr data"
        client = flickr.FlickrClient(
            settings.FLICKR_API_KEY,
            settings.FLICKR_USER_ID
        )
        client.sync()
