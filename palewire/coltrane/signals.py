from django.db.models import signals
from django.dispatch import dispatcher

from django.contrib.contenttypes.models import ContentType


def create_ticker_item(sender, instance, signal, *args, **kwargs):
	"""
	If the object being saved is a new creation, it will be added to Ticker model, and therefore the site's front page.
	"""
	from coltrane.models import Ticker
	# Check to see if the object was just created for the first time
	if 'created' in kwargs:
		if kwargs['created']:
			ctype = ContentType.objects.get_for_model(instance)
			pub_date = instance.pub_date
			Ticker.objects.get_or_create(content_type=ctype, object_id=instance.id, pub_date=pub_date)


def delete_ticker_item(sender, instance, signal, *args, **kwargs):
	from coltrane.models import Ticker
	ctype = ContentType.objects.get_for_model(instance)
	pub_date = instance.pub_date
	try:
		t = Ticker.objects.get(content_type=ctype, object_id=instance.id, pub_date=pub_date)
		t.delete()
	except Ticker.DoesNotExist:
		pass