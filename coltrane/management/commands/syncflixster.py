from django.conf import settings
from coltrane.utils import flixster
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync Flixster ratings'
    
    def handle(self, *args, **options):
        print "Syncing Flixster data"
        client = flixster.FlixsterClient(settings.FLIXSTER_USER)
        client.sync()
