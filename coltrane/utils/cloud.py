"""
A modification of the tag cloud utilities in django-tagging. 

Necessary so I can run a tagcloud for all the models, not just one.

Tip: It's good to submit a select_related query to avoid a ton of
database hits. This will run a join that really slims things down.

>>> cloud.calculate_cloud(TaggedItem.objects.select_related().all())
"""
import math
from django.utils.translation import ugettext as _

# Font size distribution algorithms
LOGARITHMIC, LINEAR = 1, 2


def _calculate_thresholds(min_weight, max_weight, steps):
    """
    Calculates where the breaks should be made between each of the groups 
    (a.k.a. steps) in the tag cloud. 
    """
    delta = (max_weight - min_weight) / float(steps)
    return [min_weight + i * delta for i in range(1, steps + 1)]


def _calculate_tag_weight(weight, max_weight, distribution):
    """
    Logarithmic tag weight calculation is based on code from the
    `Tag Cloud`_ plugin for Mephisto, by Sven Fuchs.

    http://www.artweb-design.de/projects/mephisto-plugin-tag-cloud
    """
    if distribution == LINEAR or max_weight == 1:
        return weight
    elif distribution == LOGARITHMIC:
        return math.log(weight) * max_weight / math.log(max_weight)
    raise ValueError(_('Invalid distribution algorithm specified: %s.') % distribution)


def _group_tagged_items(tagged_item_qs):
    """
    Accepts a queryset of TaggedItem objects, groups them by tag
    and then counts their frequency.
    
    Returns a dictionary of the results.
    """
    # Models we don't want to include in the cloud.
    # I've blacklisted the Track model because the tags occur so frequently
    # that they would dominate the cloud and push out all the other models.
    models_blacklist = ['track',]
    
    tag_count = {}
    for ti in tagged_item_qs:
        
        # If the model has been blacklisted, don't count it here.
        if ti.content_type.name in models_blacklist:
            # Just skip to the next iteration of the loop.
            continue
        # If you do count it...
        try:
            # Try to click up the dictionary count one.
            tag_count[ti.tag]['count'] += 1
        except KeyError:
            # But if the dictionary key doesn't yet exist, mint a new one.
            tag_count[ti.tag] = {'font_size': None, 'count': 1}

    return tag_count


def calculate_cloud(tagged_items, steps=4, distribution=LOGARITHMIC,
    min_count=5, qs=True):
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
    # If a queryset has been submitted, transform it into the dictionary
    # of grouped items that the formula requites
    if qs:
        tag_counts = _group_tagged_items(tagged_items)
    if not qs:
        tag_counts = dict(tagged_items)

    if len(tag_counts) > 0:

        # Loop through the tags...
        for tag, values in tag_counts.items():
            # And delete any that doesn't have the minimum count
            if values['count'] < min_count:
                del tag_counts[tag]

        # Figure out the range of values and use it to calculate the 
        # thresholds where the breaks between groups will be made.
        counts = [i['count'] for i in tag_counts.values()]
        min_weight = float(min(counts))
        max_weight = float(max(counts))
        thresholds = _calculate_thresholds(min_weight, max_weight, steps)

        # Then loop through each of the tags...
        for tag in tag_counts.keys():
            font_set = False
            # Figure out the weight for each tag.
            tag_weight = _calculate_tag_weight(tag_counts[tag]['count'], max_weight, distribution)
            # Then loop through the steps...
            for i in range(steps):
                # Until you hit the first threshold higher than the tag
                if not font_set and tag_weight <= thresholds[i]:
                    # Then stick it in that group
                    tag_counts[tag]['font_size'] = i + 1
                    # And set this flag so it stops trying to test
                    # against higher levels.
                    font_set = True

    # Reformat the dictionary as a tuple that I'd like to use in templates
    tag_list = [(k, v['font_size'], v['count']) for k,v in tag_counts.items()]
    # Sort by count, putting the largest first.
    tag_list.sort(key=lambda x: x[2], reverse=True)
    
    # Pass out the results
    return tag_list
    
    
