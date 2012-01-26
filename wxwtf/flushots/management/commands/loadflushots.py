from flushots import load
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Load flu shots data"
    
    def handle(self, *args, **kwds):
        load.model()


