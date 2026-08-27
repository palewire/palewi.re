---
title: 'Django recipe: remove newlines from a text block'
slug: django-recipe-remove-newlines-text-block
published_at: '2009-09-01T18:01:17-07:00'
---
<p>I like to keep a <a href="http://docs.djangoproject.com/en/dev/intro/tutorial01/">Django app</a> called "toolbox" or "utils" in my projects where I store odds and ends. One recent
addition is this quickie function for removing any newlines characters found in a block of text.</p>

<p>One place I find it useful is when I'm looking to dump scraped or user-submitted data to a spreadsheet or CSV.</p>

<p>Imagine a file like "toolbox/templatetags/misc_tags.py" within a Django project that looks like so:</p>

<pre lang="python">
from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import stringfilter
from django.utils.text import normalize_newlines

register = template.Library()

def remove_newlines(text):
    """
    Removes all newline characters from a block of text.
    """
    # First normalize the newlines using Django's nifty utility
    normalized_text = normalize_newlines(text)
    # Then simply remove the newlines like so.
    return mark_safe(normalized_text.replace('\n', ' '))
remove_newlines.is_safe = True
remove_newlines = stringfilter(remove_newlines)
register.filter(remove_newlines)
</pre>

<p>It then can be called in the template environment...</p>

<pre lang="html">
{% load misc_tags %}

{{ foo|remove_newlines }}
</pre>

<p>...or in the shell.</p>

<pre lang="python">
>>> from toolbox.templatetags.misc_tags import remove_newlines
>>> text = 'Line one\nLine two\rLine three\r\nLine four'
>>> remove_newlines(text)
'Line one Line two Line three Line four'
</pre>

<p>That's the whole trick. If there's something I screwed up&mdash;a common event&mdash;feel free to let me know.</p>