from django.conf import settings
from coltrane.utils import github
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Sync Github commits'

    def handle(self, *args, **options):
        print "Syncing Github data"
        client = github.GithubClient(settings.GITHUB_USER)
        client.sync()
