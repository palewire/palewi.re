---
title: 'Python recipe: calculate adjusted monthly values'
slug: python-recipe-calculate-adjusted-monthly-values
published_at: '2009-08-07T20:40:28-07:00'
---
<p>Here's a function I wrote earlier today that should calculate an adjusted monthly average, prorating a monthly number as if the month was 30 days in length. The idea is to compare numbers from different months against each other and prevent longer months from returning higher values simply because they contain more days.</p>

<p>The script is included with a variety of other math tools I've collected on Github under the name <a href="http://github.com/palewire/python-math/tree/master">python-math</a>.

<p>Per usual, if I screwed something up, just let me know. We'll get it ironed out.</p>

<pre lang="python">
import calendar
import datetime

def adjusted_monthly_value(value, dt):
    """
    Accepts a value and a datetime object, and
    then prorates the value to a 30-day figure
    depending on how many days are in the month.
    
    This can be useful for month-to-month comparisons
    in circumstances where fluctuations in the number
    of days per month may skew the analysis. 
    
    For instance, February typically has only 28 days, in 
    comparison to March, which has 31.
    
    h3. Example usage
    
        >> import calculate
        >> calculate.adjusted_monthly_value(10, datetime.datetime(2009, 4, 1))
        10.0
        >> calculate.adjusted_monthly_value(10, datetime.datetime(2009, 2, 17))
        10.714285714285714
        >> calculate.adjusted_monthly_value(10, datetime.datetime(2009, 12, 31))
        9.67741935483871
	
    h3. Documentation
	
        "calendar module":http://docs.python.org/library/calendar.html
	
    """
    # Test to make sure the first input is a number
    if not isinstance(value, (int,long,float)):
        return ValueError('Input values should be a number, your input is a %s' % type(value))
	
    # Test to make sure the second input is a date
    if not isinstance(dt, (datetime.datetime, datetime.date)):
        return ValueError('The submitted month should be a date or datetime value, you input a %s' % type(dt))
	
    # Get the length of the month
    length_of_month = calendar.monthrange(dt.year, dt.month)[1]
    
    # Determine the adjustment necessary to pro-rate the value to 30 days.
    adjustment = 30.0/length_of_month
    
    # Multiply the value against the adjustment and return the result
    return value * adjustment
</pre>