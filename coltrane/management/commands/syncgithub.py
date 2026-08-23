import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from coltrane.utils import github

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync Github commits"

    def handle(self, *args, **options):
        logger.debug("Syncing Github data")
        client = github.GithubClient(settings.GITHUB_USER)
        client.sync()
