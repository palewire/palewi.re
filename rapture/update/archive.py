import os
import sys
import datetime
import urllib
from BeautifulSoup import BeautifulSoup
from rapture.toolbox._mkdir import _mkdir
from copy import copy


def get_explanations(html_dir):
    """
    Quickly download the html with category explanations. 
    
    We won't parse it, but we'll save it.
    """
    url = 'http://www.raptureready.com/rap7.html'
    http = urllib.urlopen(url)
    soup = BeautifulSoup(http)
    outfile_path = os.path.join(html_dir, 'rap7.html')
    outfile = open(outfile_path, 'w')
    print >> outfile, soup.prettify()


def archive(data_dir, start_date):
    """
    Visits the Rapture Ready Index and archive the site.

    Returns a BeautifulSoup object with the HTML in it and the path to the flat files.
    """
    # Visit the URL and snatch the HTML
    url = 'http://www.raptureready.com/rap2.html'
    http = urllib.urlopen(url)
    html = http.read()
    soup = BeautifulSoup(html)

    # Save the html in our archive
    html_dir = os.path.join(data_dir, str(start_date.date()), str(start_date.strftime('%H:%M:%S')))
    _mkdir(html_dir)
    outfile_path = os.path.join(html_dir, 'rap2.html')
    outfile = open(outfile_path, 'w')
    print >> outfile, html
    
    # Create a list of all the resources the page calls
    # that we want to download so we can recreate it later.
    resources = []
    
    # Images
    for img in soup.findAll("img", {"src":True}):
        resources.append(img["src"])
        
    # Cascading Style Sheets
    for link in soup.findAll("link", {"rel":"stylesheet", "type":"text/css"}):
        resources.append(link["href"])

    # Alternative Cascading Style Sheets
    for link in soup.findAll("link", {"rel":"alternate stylesheet", "type":"text/css"}):
        resources.append(link["href"])
        
    # Download all the images to the archive.
    for r in resources:
        # Split the relative path to the img
        head, tail = os.path.split(r)

        # Create a directory to store the file
        r_dir = os.path.join(html_dir, head)
        _mkdir(r_dir)
        
        # Path together an absolute URL we can download
        url = 'http://www.raptureready.com/' + r
        local_path = os.path.join(r_dir, tail)
        urllib.urlretrieve(url, local_path)
        
    # Snatch the explanation file while we're at it.
    get_explanations(html_dir)
        
    return soup, html_dir
    
if __name__ == '__main__':
    html_path = archive()
