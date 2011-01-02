from django.conf import settings
from coltrane.utils import twitter
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync Twitter updates'

    def handle(self, *args, **options):
        print "Syncing Twitter data"
        client = twitter.TwitterClient(settings.TWITTER_USER)
        client.sync()



