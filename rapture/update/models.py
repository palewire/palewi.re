# Helpers
import os
from django.db import models
from django.utils.translation import ugettext_lazy as _

# Managers
from rapture.update.managers import *


class UpdateLog(models.Model):
    """
    A log of updates.
    """
    # When the update happened
    start_date = models.DateTimeField(help_text=_('When the update process began.'))
    end_date = models.DateTimeField(help_text=_('When the update process finished.'), null=True, blank=True)
    
    # How the update went
    archive_path = models.CharField(max_length=1000, null=True, blank=True, help_text=_('Where the files harvested by the scrape are stored.'))
    OUTCOME_CHOICES = (
        ('incomplete', 'incomplete'),
        ('complete', 'complete'),
    )
    outcome = models.CharField(max_length=20, default='incomplete', choices=OUTCOME_CHOICES, help_text=_('How the update turned out.'))
    loaded_new_data = models.NullBooleanField(default=None, help_text=_('Indicates whether the update loaded any new data to our database.'))
    
    # Meta
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    
    # Managers
    objects = LiveUpdateManager()
    
    class Meta:
        app_label = 'rapture'
        db_table = 'rapture_update_log'
        get_latest_by = 'end_date'
        verbose_name_plural = _('update log')
    
    @models.permalink
    def get_absolute_url(self):
        return ('rapture-archive-detail', [str(self.id)])

    def get_relative_archive_path(self):
        if not self.archive_path:
            return None
        else:
            return os.path.join(str(self.start_date.date()), str(self.start_date.strftime('%H:%M:%S')), 'rap2.html')

    @models.permalink
    def get_iframe_url(self):
        if not self.archive_path:
            return None
        else:
            html_path = os.path.join(str(self.start_date.date()), str(self.start_date.strftime('%H:%M:%S')), 'rap2.html')
            return ('rapture-archive-media', [html_path])
