from django.conf import settings
from coltrane.utils import delicious
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync delicious bookmarks'

    def handle(self, *args, **options):
        print "Syncing Delicious data"
        client = delicious.DeliciousClient(
            settings.DELICIOUS_USER,
            settings.DELICIOUS_PASSWORD
        )
        client.sync()
