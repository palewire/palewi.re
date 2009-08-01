"""
A modification of the tag cloud utilities in django-tagging. 

Necessary so I can run a tagcloud for all the models, not just one.

Tip: It's good to submit a select_related query to avoid a ton of
database hits. This will run a join that really slims things down.

>>> cloud.calculate_cloud(TaggedItem.objects.select_related().all())
"""
import math

# Font size distribution algorithms
LOGARITHMIC, LINEAR = 1, 2

def _calculate_thresholds(min_weight, max_weight, steps):
	delta = (max_weight - min_weight) / float(steps)
	return [min_weight + i * delta for i in range(1, steps + 1)]

def _calculate_tag_weight(weight, max_weight, distribution):
	"""
	Logarithmic tag weight calculation is based on code from the
	`Tag Cloud`_ plugin for Mephisto, by Sven Fuchs.

	.. _`Tag Cloud`: http://www.artweb-design.de/projects/mephisto-plugin-tag-cloud
	"""
	if distribution == LINEAR or max_weight == 1:
		return weight
	elif distribution == LOGARITHMIC:
		return math.log(weight) * max_weight / math.log(max_weight)
	raise ValueError(_('Invalid distribution algorithm specified: %s.') % distribution)

def _group_tagged_items(tagged_item_qs):
	"""
	Accepts a queryset of TaggedItem objects, groups them by tag, and then counts their frequency.
	"""
	tag_count = {}
	for ti in tagged_item_qs:
		try:
			tag_count[ti.tag]['count'] += 1
		except KeyError:
			tag_count[ti.tag] = {'font-size': None, 'count': 1}
	return tag_count

def calculate_cloud(tagged_items_qs, steps=4, distribution=LOGARITHMIC, min_count=5):
	"""
	Add a ``font_size`` attribute to each tag according to the
	frequency of its use, as indicated by its ``count``
	attribute.

	``steps`` defines the range of font sizes - ``font_size`` will
	be an integer between 1 and ``steps`` (inclusive).

	``distribution`` defines the type of font size distribution
	algorithm which will be used - logarithmic or linear. It must be
	one of ``tagging.utils.LOGARITHMIC`` or ``tagging.utils.LINEAR``.
	"""
	tag_counts = _group_tagged_items(tagged_items_qs)

	if len(tag_counts) > 0:
		counts = [i['count'] for i in tag_counts.values()]
		min_weight = float(min(counts))
		max_weight = float(max(counts))
		thresholds = _calculate_thresholds(min_weight, max_weight, steps)
		for tag in tag_counts.keys():
			font_set = False
			tag_weight = _calculate_tag_weight(tag_counts[tag]['count'], max_weight, distribution)
			for i in range(steps):
				if not font_set and tag_weight <= thresholds[i]:
					tag_counts[tag]['font_size'] = i + 1
					font_set = True
					
	tag_list = [(k, v['font_size'], v['count']) for k,v in tag_counts.items() if v['count'] > min_count]
	tag_list.sort(lambda x,y:cmp(x[2], y[2]))
	tag_list.reverse()
	return tag_list