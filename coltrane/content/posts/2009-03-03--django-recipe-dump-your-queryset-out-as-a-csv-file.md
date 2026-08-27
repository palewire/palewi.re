---
title: 'Django recipe: Dump your QuerySet out as a CSV file'
slug: django-recipe-dump-your-queryset-out-as-a-csv-file
published_at: '2009-03-03T13:53:00-08:00'
---
<p>I am lucky to work with really smart people. And part of what makes it fun is that they like to do data stuff. But they don't like to do Django. At least yet. They like SAS and Access and Excel and all the usual toys. So one thing I'm doing all the time is dumping data out of my systems into neutral formats for them to muck with. Here's a quick and dirty script I use that will take in a Django QuerySet and output a CSV file. It's lifted mainly from <a href="http://www.djangosnippets.org/snippets/790/">this awesome Django snippet from zbyte64</a>.</p>

<pre lang="Python">
import csv
from django.db.models.loading import get_model

def dump(qs, outfile_path):
	"""
	Takes in a Django queryset and spits out a CSV file.
	
	Usage::
	
		>> from utils import dump2csv
		>> from dummy_app.models import *
		>> qs = DummyModel.objects.all()
		>> dump2csv.dump(qs, './data/dump.csv')
	
	Based on a snippet by zbyte64::
		
		http://www.djangosnippets.org/snippets/790/
	
	"""
        model = qs.model
	writer = csv.writer(open(outfile_path, 'w'))
	
	headers = []
	for field in model._meta.fields:
		headers.append(field.name)
	writer.writerow(headers)
	
	for obj in qs:
		row = []
		for field in headers:
			val = getattr(obj, field)
			if callable(val):
				val = val()
			if type(val) == unicode:
				val = val.encode("utf-8")
			row.append(val)
		writer.writerow(row)

</pre>

<p>Per usual. Let me know what sucks.</p>