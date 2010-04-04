# Helpers
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.text import truncate_words
from django.template.defaultfilters import date as date_format

# Signals
from django.db.models import signals
from rapture.data.signals import count_scores


class Category(models.Model):
    """
    A indicator of the rapture listed on the Rapture Index.
    """
    name = models.CharField(max_length=20, primary_key=True, help_text=_('The name of the category'))
    slug = models.SlugField(unique=True, help_text=_('A stripped version of the name for URL strings'))
    explanation = models.TextField(help_text=_('An explanation of the category provided by the editors of Rapture Ready.'), null=True, blank=True)
    # Meta
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        app_label = 'rapture'
        ordering = ['name']
        verbose_name_plural = _('categories')
        db_table = 'rapture_data_category'

    def __unicode__(self):
        return self.name

    def get_short_explanation(self, words=10):
        return truncate_words(self.explanation, words)
    short_explanation = property(get_short_explanation)


class Edition(models.Model):
    """
    A release of the Rapture Index
    """
    date = models.DateField(verbose_name=_('Publication date'))
    total = models.IntegerField(default=None, null=True, blank=True, editable=False, verbose_name=_('Total Rapture Index score'))
    PROPHETIC_ACTIVITY_CHOICES = (
        ('slow', '100 and Below: Slow prophetic activity'),
        ('moderate', '100 to 130: Moderate prophetic activity'),
        ('heavy', '130 to 160: Heavy prophetic activity'),
        ('seat-belts', 'Above 160: Fasten your seat belts'),
        ('unclassified', 'Unclassified'),
    )
    prophetic_activity = models.CharField(max_length=50, choices=PROPHETIC_ACTIVITY_CHOICES, default='unclassified')
    # Meta
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        app_label = 'rapture'
        ordering = ['-date']
        get_latest_by = ['-date']
        db_table = 'rapture_data_edition'

    def __unicode__(self):
        return u'%s (%s)'  % (str(self.date), self.total)

    def get_total(self):
        return sum([i.score for i in self.score_set.all() if i.score >= 0])
        
    def get_prophetic_activity(self):
        """
        Returns the level of prophetic activity based on the total, using standards set by the Rapture Ready editors.
        """
        if not self.total:
            return 'unclassified'
        elif self.total > 160:
            return 'seat-belts'
        elif self.total > 130:
            return 'heavy'
        elif self.total > 100:
            return 'moderate'
        else:
            return 'slow'


class Score(models.Model):
    """
    The score registered by an Indicator in a particular Edition.
    """
    edition = models.ForeignKey(Edition, help_text=_('The edition this score was released.'))
    category = models.ForeignKey(Category, help_text=_('The indicator this score is for.'))
    score = models.IntegerField(help_text=_('The score, ranging from 1-5'))
    comment = models.TextField(help_text=_('An explanation of this score given by the editors of Rapture Ready.'), null=True, blank=True)
    #is_amended = models.BooleanField(default=False, help_text=_('Indicates if the score has been replaced with updated information.'))
    # Meta
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        app_label = 'rapture'
        ordering = ('category', 'edition')
        db_table = 'rapture_data_score'

    def __unicode__(self):
        return u'%s: %s (%s)' % (self.category.name, self.score, date_format(self.edition.date, 'N d, Y'))


# Rerun the totals for each Edition whenever a Score is saved or deleted.
signals.post_save.connect(count_scores, sender=Score)
signals.post_delete.connect(count_scores, sender=Score)
