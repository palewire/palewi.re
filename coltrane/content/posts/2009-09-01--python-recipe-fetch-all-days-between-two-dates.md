---
title: 'Python recipe: fetch all the days between two dates'
slug: python-recipe-fetch-all-days-between-two-dates
published_at: '2009-09-01T10:32:05-07:00'
---
<p>I've added a new function to my <a href="http://github.com/palewire/python-math/tree/master">python-math library</a> that will return a list&mdash;technically a <a href="http://www.wellho.net/mouth/561_Python-s-Generator-functions.html">generator</a>&mdash;of all of the days between two dates.</p>

<p>There might be a more obvious way to do this, but I don't know it. If you do, please let me know.</p>

<pre lang="python">
import datetime

def date_range(start_date, end_date):
    """
    Returns a generator of all the days between two date objects.
    
    Results include the start and end dates.
    
    Arguments can be either datetime.datetime or date type objects.
    
    h3. Example usage
    
        >>> import datetime
        >>> import calculate
        >>> dr = calculate.date_range(datetime.date(2009,1,1), datetime.date(2009,1,3))
        >>> dr
        <generator object at 0x718e90>
        >>> list(dr)
        [datetime.date(2009, 1, 1), datetime.date(2009, 1, 2), datetime.date(2009, 1, 3)]
        
    """
    # If a datetime object gets passed in,
    # change it to a date so we can do comparisons.
    if isinstance(start_date, datetime.datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime.datetime):
        end_date = end_date.date()
    
    # Verify that the start_date comes after the end_date.
    if start_date > end_date:
        raise ValueError('You provided a start_date that comes after the end_date.')
    
    # Jump forward from the start_date...
    while True:
        yield start_date
        # ... one day at a time ...
        start_date = start_date + datetime.timedelta(days=1)
        # ... until you reach the end date.
        if start_date > end_date:
            break

</pre>