import os
import boto
from datetime import datetime
from datetime import timedelta
from django.conf import settings
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = '<date YYYY-MM-DD>'
    help = 'Load a database snapshot from our nightly archive. Pulls latest by default. Specify date for an older one.'

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            action="store",
            dest="name",
            default='',
            help="A custom name for the database we're creating"
        )

    def handle(self, *args, **options):
        # If the user provides a date, try to use that
        if args:
            try:
                dt = datetime.strptime(args[0], '%Y-%m-%d')
            except ValueError:
                raise CommandError("The date you submitted is not valid.")
        # Otherwise just use the today minus one day
        else:
            dt = datetime.now().date() - timedelta(days=1)

        # Download the snapshot
        filename = self.download(dt.strftime("%Y-%m-%d"))

        # Load the snapshot into the database
        target = options.get('name') or "palewire_%s" % dt.strftime("%Y-%m-%d")
        self.load(target, filename)

    def load(self, target, source):
        """
        Load a database snapshot into our postgres installation.
        """
        # Set some vars
        os.environ['PGPASSWORD'] = settings.DATABASES['default']['PASSWORD']
        user = settings.DATABASES['default']['USER']
        print "Loading to new database %s" % target
        # If the db already exists, we need to drop it.
        try:
            os.system("dropdb -U %s %s" % (user, target))
        except:
            pass
        # Create the database
        os.system("createdb -U %s %s" % (user, target))
        # Load the data
        os.system("pg_restore -U %s -Fc -d %s ./%s" % (user, target, source))
        # Delete the snapshot
        os.system("rm ./%s" % source)

    def download(self, dt):
        """
        Download a database snapshot.
        """
        # Craft up what the beginning of the snapshot should be
        prefix = 'postgres_palewire_%s' % dt

        # Log into our bucket
        conn = boto.connect_s3(
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY
        )
        bucket = conn.get_bucket("palewire-backups")
        # Loop through all of the objects and look for a match
        for obj in bucket.list():
            k = str(obj.key)
            if k.startswith(prefix):
                print "Downloading %s" % k
                # If you find it, download it
                obj.get_contents_to_filename(k)
                return k
        raise CommandError("The date you provided could not be found in the archive.")
