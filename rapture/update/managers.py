from django.db import models
from rapture.update.models import *


class LiveUpdateManager(models.Manager):
    """
    Returns the latest live updates.
    
    Example usage:
        
        >>> UpdateLog.objects.complete()
        >>> UpdateLog.objects.updates()
        >>> UpdateLog.objects.last_scraped()
        >>> UpdateLog.objects.last_updated()
        
    """
    def complete(self):
        return self.filter(outcome='complete')

    def updates(self):
        return self.filter(outcome='complete', loaded_new_data=True)

    def last_scraped(self):
        """
        Return the date of the last the source was scraped.
        """
        try:
            latest_obj = self.complete().latest()
            return latest_obj.end_date
        except UpdateLog.DoesNotExist:
            return None

    def last_updated(self):
        """
        Returns the date of the last time the data were modified.
        """
        try:
            latest_obj = self.updates().latest()
            return latest_obj.end_date
        except UpdateLog.DoesNotExist:
            return None
