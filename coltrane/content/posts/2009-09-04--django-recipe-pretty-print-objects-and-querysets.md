---
title: 'Django recipe: Pretty print objects and querysets'
slug: django-recipe-pretty-print-objects-and-querysets
published_at: '2009-09-04T13:41:03-07:00'
---
<p>Below you can find a utility I use across Django projects called dprint. It's a simple addition to the excellent <a href="http://docs.python.org/library/pprint.html">pprint library</a> that will spit your Django objects and querysets out as dictionaries. The result is that the data are a bit easier to browse while debugging. Or at least I think so.</p>

<p>The odds that I screwed something up or there's an easier way to do this are pretty high. Feel free to tell me about it.</p>

<pre lang="python">
from django.db.models.query import QuerySet
from pprint import PrettyPrinter

def dprint(object, stream=None, indent=1, width=80, depth=None):
    """
    A small addition to pprint that converts any Django model objects to dictionaries so they print prettier.

    h3. Example usage

        >>> from toolbox.dprint import dprint
        >>> from app.models import Dummy
        >>> dprint(Dummy.objects.all().latest())
         {'first_name': u'Ben',
          'last_name': u'Welsh',
          'city': u'Los Angeles',
          'slug': u'ben-welsh',
    """
    # Catch any singleton Django model object that might get passed in
    if getattr(object, '__metaclass__', None):
        if object.__metaclass__.__name__ == 'ModelBase':
            # Convert it to a dictionary
            object = object.__dict__
    
    # Catch any Django QuerySets that might get passed in
    elif isinstance(object, QuerySet):
        # Convert it to a list of dictionaries
        object = [i.__dict__ for i in object]
        
    # Pass everything through pprint in the typical way
    printer = PrettyPrinter(stream=stream, indent=indent, width=width, depth=depth)
    printer.pprint(object)
</pre>

