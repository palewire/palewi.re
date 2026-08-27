---
title: 'Python recipe: print a future date in the format you want'
slug: python-recipe-print-a-future-date-in-the-format-you-want
published_at: '2008-04-21T10:31:59-07:00'
wordpress_id: 109
---
<p>Enough with all the talky talky, here's a simple snippet I cooked up for a friend this morning to solve his problem of the moment: how to coax Python into printing out a future date (6 weeks in the future, to be exact) in the format he wants. Hope it's useful to somebody. Let me know if I screwed anything up.</p>



<pre lang="Python">
>>> import datetime
>>> now = datetime.datetime.now()
>>> print now
2008-04-21 10:19:35.832928
>>> from datetime import timedelta
>>> diff = datetime.timedelta(days=42)
>>> print diff
42 days, 0:00:00
>>> print now + diff
2008-06-02 10:19:35.832928
>>> future = now + diff
>>> future.strftime("%m/%d/%Y")
'06/02/2008'</pre>

<p>Documentation on how you can customize strftime to print dates in the format you need can be found <a href="http://docs.python.org/lib/module-time.html">here</a>. Scroll down to the middle-ish part of the page.</p>