from django.db.models import signals
from django.dispatch import dispatcher

def count_scores(sender, instance, signal, *args, **kwargs):
    """
    Runs through all the editions and adds up their current scores.
    """
    from rapture.data.models import Edition
    for edition in Edition.objects.all():
        edition.total = edition.get_total()
        edition.prophetic_activity = edition.get_prophetic_activity()
        edition.save()
