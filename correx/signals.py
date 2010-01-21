

def count_changes(sender, instance, signal, *args, **kwargs):
	"""
	Runs through all the change types and adds up their current numbers
	"""
	from correx.models import ChangeType
	for change_type in ChangeType.objects.all():
		change_type.count_changes()