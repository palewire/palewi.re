import os
import sys
import re
import time
import datetime
import urllib
from BeautifulSoup import BeautifulSoup
from django.utils.text import normalize_newlines, force_unicode
from rapture.toolbox.remove_newlines import remove_newlines
from rapture.toolbox.dprint import dprint


def text2date(text):
    """
    Converts the date strings published by Rapture Ready into a datetime.date object.
    """
    text = text.strip()
    text = text.replace('&nbsp;', '')
    time_tuple = time.strptime(text + '10', '%b %d, %Y')
    return datetime.date(*(time_tuple[0:3]))

def strip_html(text):
    return re.sub(r'<[^>]*?>', '', text)

def parse_score(text):
    """
    Pulls apart the score provided by Rapture Ready in cases where they include a `+` or a `-`
    to indicate changes from the last list.
    """
    text = text.strip()
    # Scores range from 1 to 5, so we should expect typical score to only be one character in length.
    # And since we only need that first character, we can just snap it from the rest each time,
    # regardless of how long the string might be.
    try:
        text = text[0]
    except IndexError:
        text = -1
        print "BAD SCORE! CHECK THE DATA!"
    return text

def clean_comment(pair):
    """
    Cleans the bits scraped from the comments section.
    """
    pair = [remove_newlines(i) for i in pair]
    pair = [i.strip() for i in pair]
    # Remove colons
    pair[0] = pair[0].replace(':', '')
    # Remove excess whitespace
    whitespace_regex = re.compile('\s\s+')
    pair[1] = whitespace_regex.sub(' ', pair[1])
    return pair

def parse(soup):
    
    # Narrow down to the table containing the rankings
    table = soup.find('table', attrs={
     'border': '0',
     'cellspacing': '6',
    })
    # Split the three columns into entries in a list
    column_list = table.findAll('table')
    # Initialize a dictionary for storing the results
    scores_dict = {}
    # Create a regex for picking through the wacky way they print the scores.
    score_regex = re.compile('^\\n?<!-(.*)->(?P<score>(.*))$')
    # Loop through the columns
    for column in column_list:
        # Make a list of the entries in the order they appear.
        entries = [li.font.string.strip() for li in column.findAll('li')]
        # Grab the <td> tag that contains the scores.
        scores_table = column.find('td', attrs={'width': '14%'})
        # Smush all the HTML into one big string
        scores_string = "".join(map(str, scores_table.font.contents))
        # Split that HTML on <br> tags and use the regex to snatch out the scores.
        split_strings = scores_string.split('<br />')
        scores = []
        for string in split_strings:
            try:
                score = score_regex.search(string).group('score').strip()
            except:
                if string[-2] in ['-', '+']:
                    score = string[-3]
                else:
                    score = string[-1]
            scores.append(score)
        # Loop through the entries
        for i, entry in enumerate(entries):
            # And assign it with its corresponding score to our data dictionary.
            # Since they occur in the same order, we can use enumerate to pull
            # the same index value from the other set.
            scores_dict[entry] = parse_score(scores[i])

    # Use a regex to snag the line where the update date is published, and then walk up to the parent HTML tag
    timestamp_html = soup.find(text=re.compile('Updated')).parent
    # Smush all the html in the tag into a big string, stripping out the html
    timestamp_string = strip_html("".join(map(force_unicode, timestamp_html)))
    # Split the string on 'updated' and grab the other half, stripping out all the whitespace.
    # And then pass it to our conversion function that will translate the string into a date object.
    timestamp = text2date(timestamp_string.split('Updated')[1].strip())

    # Pull the HTML block that holds comments associted with sources
    comments = soup.find('pre', attrs={'class': 'style1'})
    # Standardize the newlines so I can be confident in my regexes
    comments = normalize_newlines(comments.contents[0])
    # Make a regex that will catch the category numbers
    two_digits = re.compile('\n\d{2} ')
    # Use it to the split the HTML block
    comments = two_digits.split(comments)
    # Break the items in half, using the newline we expect to separate the category from the comment
    comments = [i.split('\n', 1) for i in comments]
    # Run a number of routine cleanup operations
    comments = [clean_comment(i) for i in comments]
    # Filter out any empty entires
    comments = [i for i in comments if i[0]]
    # Load the results into a dictionary
    comments_dict = {}
    for category, comment in comments:
        comments_dict[category] = comment
        
    # Return the dictionary of scores along with the timestamp in a tuple
    return scores_dict, comments_dict, timestamp
    
