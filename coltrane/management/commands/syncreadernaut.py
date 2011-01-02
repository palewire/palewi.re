from django.conf import settings
from coltrane.utils import readernaut
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync Readernaut books'

    def handle(self, *args, **options):
        print "Syncing Readernaut data"
        client = readernaut.ReadernautClient(settings.READERNAUT_USER)
        client.sync()



