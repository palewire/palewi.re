import os
import subprocess
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Syncs the static directory to Amazon S3"

    def handle(self, *args, **kwds):
        if not os.path.exists(settings.STATIC_ROOT):
            raise CommandError("Static directory does not exist. Cannot publish something before you build it.")
        cmd = "s3cmd sync --delete-removed --no-mime-magic --force --acl-public %s/ s3://%s"
        subprocess.call(cmd % (settings.STATIC_ROOT, settings.AWS_BUCKET_NAME),
            shell=True)
