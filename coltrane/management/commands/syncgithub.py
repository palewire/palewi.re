import logging

logger = logging.getLogger(__name__)
from django.conf import settings
from coltrane.utils import github
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Sync Github commits"

    def handle(self, *args, **options):
        logger.debug("Syncing Github data")
        client = github.GithubClient(settings.GITHUB_USER)
        client.sync()
