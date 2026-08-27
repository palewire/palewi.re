---
title: 'Python recipe: Grab page, scrape table, download file'
slug: python-recipe-grab-a-page-scrape-a-table-download-a-file
published_at: '2008-04-20T13:43:13-07:00'
wordpress_id: 107
---
<p>Here's a change of pace. Our <a href="http://www.palewire.com/2008/04/05/python-recipe-open-a-file-read-through-it-print-each-line-matching-a-search-term/">first</a> <a href="http://www.palewire.com/2008/04/07/python-recipe-open-multiple-files-search-for-matches-count-your-hits-on-the-fly/">few</a> <a href="http://www.palewire.com/2008/04/14/python-recipe-read-a-file-search-for-a-pattern-print-your-matches/">lessons</a> focused on how you can use Python to goof with a bunch of local files. This time we're going to try something different: using Python to go online and screw around with the Web. </p>



<p>Whenever I caucus with aspiring <a href="http://www.google.com/url?sa=t&ct=res&cd=1&url=http%3A%2F%2Fwww.nicar.org%2F&ei=1HYLSJWzII6IiwGuhvj7Ag&usg=AFQjCNFv1OMXDU_2U5mOn6I-DfJcHnfT7Q&sig2=PRhstdzVRiSElCZCCA9pQA">NICARians</a> and other data hungry reporters, it's not long before the topic of <a href="http://en.wikipedia.org/wiki/Web_scraping">web scraping</a> comes up. While automated text processing and database management may sound well and good, there's something sexy about pulling down a fatty government database that catches people's imagination and inspires them to take on the challenge of learning a new programming language. Or at least entertain the idea until they run into a road block.</p>



<p>A number of fellow travelers do a noble job instructing people on the basics during NICAR's annual seminars. But scraping seems like such a sought-after skill that it feels like a good idea to throw up a basic walkthrough here, where beginners can cut and paste code and any feedback can be memorialized. </p>



<p>But before we get going, let me just say that I'm going to assume you read the first couple recipes and won't be working too hard to explain the stuff covered there. And keep in mind that my keystrokes are coming right off my home computer, which runs Ubuntu Linux. I'll try to provide Mac and Windows translations as we go, but I might muck a phoneme here and there. If anything is screwed up and doesn't work on your end, just shoot me an email or drop a comment. We'll iron it out.</p>



<p>Formalities aside, here's the example task I've selected to achieve our mission.</p>



<ol>

	<li>Install the necessary Python modules, mechanize and Beautiful Soup.</li>

	<li>Train our computer to visit Ben's list of <a href="http://www.palewire.com/scrape/albums/2007.html">The Greatest Albums in the History of 2007</a>.</li>

	<li>Parse the html and scrape out Ben's rankings.</li>

	<li>Click through to Ben's list of <a href="http://www.palewire.com/scrape/albums/2006.html">The Greatest Albums in the History of 2006</a> and repeat the scrape.</li>

        <li>Do it all over again, but this time download the cover art.</li>

</ol>



<h2>1. Download the mechanize and Beautiful Soup modules. Install them. </h2>



<p>There are a dozen different methods for going about our task, so you shouldn't assume the one I'm about to show you is the only or the best. It's just one way to do it. And doing it this way requires a couple additions to your Python installation, which might seem a little daunting but should be doable unless IT has your computer on double secret probation. </p>



<p>A <a href="http://www.python.org/doc/2.0.1/tut/node8.html">module</a> is a collection of functions, defintions and statements contained in a separate file that you can import into your script. Examples native to Python used in our earlier scripts included "re", "os" and "string." </p>



<p>Out there on the Web, kind and ambitious programmers are constantly drafting, updating and publishing new modules to boil down complicated tasks into simpler forms. It it wasn't for these people, praise be upon them, I probably wouldn't have a job. </p>



<p>If you want to take advantage of their contributions, you need to plug their creations into your local Python installation. It's usually not that hard, even on Windows!</p>



<p>To accomplish today's task, we're going to rely on two third-party modules. The first is <a href="http://www.google.com/url?sa=t&ct=res&cd=1&url=http%3A%2F%2Fwwwsearch.sourceforge.net%2Fmechanize%2F&ei=WokLSJr3A52qiAHS6L38Ag&usg=AFQjCNGUEUs6Jn1FSoo0YYjpZ2PJe6E6Ag&sig2=I3rdoLQ5AV843Eignvjxgg">mechanize</a>, a Python translation of <a href="http://www.google.com/url?sa=t&ct=res&cd=1&url=http%3A%2F%2Fsearch.cpan.org%2Fdist%2FWWW-Mechanize%2F&ei=gIkLSOmaMY-ShAOc38TDAw&usg=AFQjCNEsooTEHj6bN2UHDi0OfZ2krEX-EA&sig2=zPl5yUdSVr0loDl4qaaUYQ">the popular Perl module</a> for calling up and walking through Web pages. The second is <a href="http://www.google.com/url?sa=t&ct=res&cd=1&url=http%3A%2F%2Fwww.crummy.com%2Fsoftware%2FBeautifulSoup%2F&ei=tIkLSITRIYjGigHqmez7Ag&usg=AFQjCNHAxwplurFOBqg5cehWQEVKi-TuLQ&sig2=UhVMcFqeJrnKIp2wIF5t6g">Beautiful Soup</a>, a superlatively elegant means for parsing HTML and XML documents. Working hand-in-hand, they can accomplish most simple web scrapes.</p>



<p>If you're working Linux or Mac OS X, this is going to be a piece of cake. All you need is to use Python's auto-installer <a href="http://peak.telecommunity.com/DevCenter/EasyInstall">Easy Install</a> to issue the following commands:</p>



<pre lang="Bash">sudo easy_install mechanize
sudo easy_install BeautifulSoup</pre>



<p>And now you can check if the modules are available for use by cracking open your python interpreter...</p>



<pre lang="Bash">python</pre>



<p>...and attempting to import the new modules...</p>



<pre lang="Python">
from mechanize import Browser
from BeautifulSoup import BeautifulSoup</pre>



<p>If the interpreter accepts the commands and kicks down the next line without an error, you know you're okay. If it throws an error, you know something is off. </p>



<p>I don't have a lot of Python experience working in Windows, but the method for adding modules that I've had success with is simply downloading the .py files to my desktop and dumping them in the "lib" folder of my Python installation. If, like me, you use Activestate's <a href="http://www.activestate.com/Products/activepython/?_x=1">ActivePython</a> distribution for Windows, it should be easily found at C:/Python25/lib/. And when you browse around the directory, you should already see os.py, re.py and other modules we're already familar with. So just visit the <a href="http://wwwsearch.sourceforge.net/mechanize/">mechanize</a> and <a href="http://www.crummy.com/software/BeautifulSoup/">Beautiful Soup</a> homepages and retrieve the latest download. Dump the .py files in your lib folder and now you should be able to fire up your python interpreter just the same as above and introduce yourself to our new friends.</p>



<p>With that out of the way, we now have all the tools we need to grip and rip. So let's do it!</p>



<h2>2. Open the command line, create a working directory, move there.</h2>



<p>We're going to start the same way we did in the first three lessons, creating a working folder for all our files and moving in with our command line.</p>



<pre lang="Bash">cd Documents/
mkdir py-scrape-and-download
cd py-scrape-and-download/</pre>



<p>The commands should work just as easily in Mac as in Linux. If you're working in Windows, you'll be on the C:/ file structure, rather than the Unix-style structure above. So you might mkdir a new working directory in your C:/TEMP folder or wherever else you'd like to work. Or just make a folder wherever through Windows Explorer and cd there after the fact through the command line.</p>



<h2>3. Create our python script in the text editor of your choice.</h2>



<pre lang="Bash">vim py-scrape-and-download.py</pre>



<p>The line above, which again should work for Linux or Mac, will open a new file in <a href="http://www.google.com/url?sa=t&ct=res&cd=1&url=http%3A%2F%2Fwww.vim.org%2F&ei=uzoESIj8LKnmpgTRy43VBw&usg=AFQjCNE8C6iOb5uQLy74YKg-WBd9hikKaw&sig2=vP2XqMTTDBFF49Gy22gxJQ">vim</a>, the command-line text editor that I prefer. You can follow along, or feel free to make your own file in the application you prefer. If you're a newbie Windows user, <a href="http://www.google.com/url?sa=t&ct=res&cd=1&url=http%3A%2F%2Fen.wikipedia.org%2Fwiki%2FNotepad&ei=zToESKWNL4uqpwT2k73dBw&usg=AFQjCNEXWgXDcow8vXjueJBIOmWghv1lhw&sig2=aDintKlEbbRHHWcaHXoz1w">Notepad</a> should work great.</p>



<p>If you're following along in vim, you'll need to enter "insert mode" so you can start entering text. Do that by hitting:</p>



<pre lang="Bash">i</pre>



<h2>4. Write the code!</h2>



<pre lang="Python">#!/usr/bin/env python
from mechanize import Browser
from BeautifulSoup import BeautifulSoup

mech = Browser()
url = "http://www.palewire.com/scrape/albums/2007.html"
page = mech.open(url)
html = page.read()

soup = BeautifulSoup(html)
print soup.prettify()</pre>



<p>Our first snippet of code, seen above, shows a basic introduction to each of our new modules.</p>



<p>After they've been imported in lines two and three, we put mechanize's browser to use right away, storing it a variable I've decided to call mech, but which you could call anything you wanted (ex. browser, br, ie, whatever). We then use its open() method to grab the location of our first scrape target, <a href="http://www.palewire.com/2008/04/14/python-recipe-read-a-file-search-for-a-pattern-print-your-matches/">my favorite albums of 2007</a>, and store that in another variable we'll call page. </p>



<p>That's enough to go out on the web and grab the page, now we need to tell Python what to do with it. Mechanize's read() method will return all of the HTML in the page, which we store, simply, in an variable called html and then pass to BeautifulSoup's default method so it can be prepared for processing.</p>



<p>The reason we need to pass the page to Beautiful Soup is that there is a ton of HTML code in the page we don't want. Our ultimate goal isn't to print out the complete page source. We don't want all the junky td and img and body tags. We want to free the data from the HTML by printing it out in a machine readable format we can repurpose for our own needs. In the next step we'll ask Beautiful Soup to step through the code and pull out only the good parts, but here in the first iteration we'll pause with just printing out the complete page code using a fun Beautiful Soup method called prettify(). It will spit out the HTML in a well-formed format. To take a look, save and quit out of your script (ESC, SHIFT+ZZ in vim) and fire it up from the command-line:</p>



<pre lang="Bash">python py-scrape-and-download.py</pre>



<p>And you should see something like....</p>



<pre lang="HTML"><html>
 <head>
  <title>
   According to Ben...
  </title>
 </head>
 <body>
  <h2>
   The 10 Greatest Albums in the History of 2007
  </h2>
  <table padding="1" width="60%" border="1" style="text-align:center;">
   <tr style="font-weight:bold">
    <td>
     Rank
    </td>
    <td>
     Artist
    </td>
...</pre>



<p>...which means that you've successfully retrieved and printed out our first target. Now let's move on to scraping the data out from the HTML.</p>



<pre lang="Python">#!/usr/bin/env python
from mechanize import Browser
from BeautifulSoup import BeautifulSoup

mech = Browser()
url = "http://www.palewire.com/scrape/albums/2007.html"
page = mech.open(url)

html = page.read()
soup = BeautifulSoup(html)
table = soup.find("table", border=1)

for row in table.findAll('tr')[1:]:
    col = row.findAll('td')
    rank = col[0].string
    artist = col[1].string
    album = col[2].string
    cover_link = col[3].img['src']
    record = (rank, artist, album, cover_link)
    print "|".join(record)</pre>

<p>The second version of our script, seen above, removes the prettify() command that concluded version one and replaces it with the Beautiful Soup code necessary to parse the rankings from the page. </p>



<p>When you're scraping a real target out there on the wild Web, the mechanize part of the script is likely to remain pretty much the same, but the Beautiful Soup portion that pulls the data from the page is going to have change each time, tailored to work with however your target HTML is structured. </p>



<p>So your job as the scraper is to inspect your target table and figure out how you can get Beautiful Soup to hone in on the elements you want to harvest. I like to do this using the Firefox plugin <a href="https://addons.mozilla.org/en-US/firefox/addon/1843">Firebug</a>, which allows you to right-click and, by choosing the "Inspect Element" option, have the browser pull up and highlight the HTML underlying any portion of the page. But all that's really necessary is that you take a look at the page's source code. </p>



<p>Since most HTML pages you'll be targeting, including my sample site, will include more than one set of table tags, you often have to find something unique about the table you're after. This is necessary so that Beautiful Soup knows how to zoom in on that section of the code you're after and ignore all the flotsam around it. </p>



<p>If you look closely at this particular page, you'll note that while both table tags have the same width value, an easy way to distinguish them is that they have different border values...</p>



<pre lang="HTML"><table width="60%" border="1" style="text-align: center;" padding="1">
...
<table width="60%" border="0"></pre>



<p>...and the one we want to harvest has a border value of one. That's why the first Beautiful Soup command seen in the snippet above uses the find() method to capture the table with that characteristic.</p>



<pre lang="Python">table = soup.find("table", border=1)</pre>



<p>Once that's been accomplished, the new table variable is immediately put to use in a loop that is designed to step through each row and pull out the data we want.</p>



<pre lang="Python">for row in table.findAll('tr')[1:]:</pre>



<p>It uses Beautiful Soup's findAll() method to put all of the tr tags (which is the HTML equivalent of a row) into a list. The [1:] modifier at the end instructs the loop to skip the first item, which, from looking at the page, we can tell is an unneeded header line. </p>



<p>Then, after the loop is set up on the tr tags, we set up another list that will grab all of the td tags (the HTML equivalent of a column) from each row. </p>



<pre lang="Python">    col = row.findAll('td')</pre>



<p>Now pulling out the data is simply a matter of figuring out which order we can expect the data to appear in each row and pulling the corresponding values from the list. Since we expect rank, artist, album and cover to appear in each row from left to right, the first element of the col variable (col[0]) can always be expected to be the rank and the last element (col[3]) can always be expected to be the cover. So we create a new set of values to retrieve each, with some Beautiful Soup specific objects tacked on the end to grab only the bits we want.</p>



<pre lang="Python">    rank = col[0].string
    artist = col[1].string
    album = col[2].string
    cover_link = col[3].img['src']</pre>



<p>The ".string" object will return the text within the target tag (similar to javascript's innerHTML method). But in the case of something like the cover art, which is an image tag, not a string value, we can step down to the next tag nested within the td column -- img -- and access its source attribute by tacking on ['src']. This would work just the same for a hyperlink (.a['href']) or any other attibute. And if you've got multiple layers of nested tags, you can simply step down through them with a linked set of objects. For example, "b.a.string" would retrieve the string within a link within a bold tag. There's great documentation on these and other Beautiful Soup tricks <a href="http://www.crummy.com/software/BeautifulSoup/documentation.html">here</a>. </p>



<p>After we've wrangled out the data we want from the HTML, the only challenge remaining is to print it out. I accomplish that above by loading the column values into a list called record and printing it out use a trick that will print them with a pipe-delimiter using the .join method.</p>



<pre lang="Python">
    record = (rank, artist, album, cover_link)
    print "|".join(record)
</pre>



<p>Phew. That's a lot of explaining. I hope it made sense. I'm happy to clarify or elaborate on any of it. But if you save the snippet above and run it. You should get a simple print out of the data that looks something like this:</p>



<pre lang="bash">10|LCD Soundsystem|Sound of Silver|http://www.palewire.com/scrape/albums/covers/sound%20of%20silver.jpg
9|Ulrich Schnauss|Goodbye|http://www.palewire.com/scrape/albums/covers/goodbye.jpg
8|The Clientele|God Save The Clientele|http://www.palewire.com/scrape/albums/covers/god%20save%20the%20clientele.jpg
7|The Modernist|Collectors Series Pt. 1: Popular Songs|http://www.palewire.com/scrape/albums/covers/collectors%20series.jpg
6|Bebel Gilberto|Momento|http://www.palewire.com/scrape/albums/covers/memento.jpg
5|Various Artists|Jay Deelicious: 1995-1998|http://www.palewire.com/scrape/albums/covers/jaydeelicious.jpg
4|Lindstrom and Prins Thomas|BBC Essential Mix|http://www.palewire.com/scrape/albums/covers/lindstrom%20prins%20thomas.jpg
3|Go Home Productions|This Was Pop|http://www.palewire.com/scrape/albums/covers/this%20was%20pop.jpg
2|Apparat|Walls|http://www.palewire.com/scrape/albums/covers/walls.jpg
1|Caribou|Andorra|http://www.palewire.com/scrape/albums/covers/andorra.jpg</pre>



<p>See the difference?! Pretty cool, right?</p>



<p>But, really, you could of done that with copy and paste. Or, if you're slick, maybe even <a href="http://articles.techrepublic.com.com/5100-10877_11-6115870.html?part=rss&tag=feed&subj=tr">Excel's Web Query</a>.</p>



<p>As with our previous recipes, the real efficiencies aren't found until you can train your computer to repeat a task over a large body of data. One of the great things mechanize can do is step through pages one by one and help Beautiful Soup suck the data out of each. This is very helpful when you're trying to scrape the search results from online web queries, which are commonly displayed in paginated sets that run into hundreds and hundreds of pages.</p>



<p>Today's example is only two pages in length, though the principles we learn here can later be applied to broader data sets. But before we can run, we have to learn how to walk. So, in that spirit, here's a simple expansion of our script above that will click on the "Next" link at the bottom of our example page and repeat the scrape on <a href="http://www.palewire.com/scrape/albums/2006.html">my 2006 list</a>.</p>



<pre lang="Python">#!/usr/bin/env python
from mechanize import Browser
from BeautifulSoup import BeautifulSoup

def extract(soup, year):
    table = soup.find("table", border=1)
    for row in table.findAll('tr')[1:]:
        col = row.findAll('td')
        rank = col[0].string
        artist = col[1].string
        album = col[2].string
        cover_link = col[3].img['src']
        record = (str(year), rank, artist, album, cover_link)
        print "|".join(record)

mech = Browser()
url = "http://www.palewire.com/scrape/albums/2007.html"
page1 = mech.open(url)
html1 = page1.read()
soup1 = BeautifulSoup(html1)
extract(soup1, 2007)
page2 = mech.follow_link(text_regex="Next")
html2 = page2.read()
soup2 = BeautifulSoup(html2)
extract(soup2, 2006)</pre>



<p>Note that our Beautiful Soup snippet remains the same as above, but we've moved it to the top of the script and placed it in a <a href="http://www.penzilla.net/tutorials/python/functions/">Python function</a> called extract. Structured this way, the extract function is reusable on any number of pages as long as the HTML you're looking to parse is formatted the same way. </p>



<p>The function accepts two parameters, soup and year, which are passed in the lower part of our script after Beautiful Soup captures each page's contents. The first snippet ...</p>



<pre lang="Python">page1 = mech.open(url)
html1 = page1.read()
soup1 = BeautifulSoup(html1)
extract(soup1, 2007)</pre>



<p>...essentially does the same thing as our early versions: visits the URL for my 2007 list and parses out the table. The only change is that the soup variable is now being passed to the extract function along with the year, so that it can be printed alongside the data columns in our output by adding it to the "record" list inside the function here:</p>



<pre lang="Python">        record = (str(year), rank, artist, album, cover_link)</pre>



<p>I figured it's a nice add since then our eventual results will contain a field that discerns the 2007 list from the 2006 list. </p>



<p>Now check out easy it is to get mechanize to step through to the next page.</p>



<pre lang="Python">page2 = mech.follow_link(text_regex="Next")
html2 = page2.read()
soup2 = BeautifulSoup(html2)
extract(soup2, 2006)</pre>



<p>All it takes is feeding the link's string value to mechanize's follow_link() method and, boom, you're walking over to the next page. Treat what you get back the same as we did our first "page" and, bam, you've done it. Save the script, run it, and you should see something more like this:</p>



<pre lang="Bash">2007|10|LCD Soundsystem|Sound of Silver|http://www.palewire.com/scrape/albums/covers/sound%20of%20silver.jpg
2007|9|Ulrich Schnauss|Goodbye|http://www.palewire.com/scrape/albums/covers/goodbye.jpg
2007|8|The Clientele|God Save The Clientele|http://www.palewire.com/scrape/albums/covers/god%20save%20the%20clientele.jpg
2007|7|The Modernist|Collectors Series Pt. 1: Popular Songs|http://www.palewire.com/scrape/albums/covers/collectors%20series.jpg
2007|6|Bebel Gilberto|Momento|http://www.palewire.com/scrape/albums/covers/memento.jpg
2007|5|Various Artists|Jay Deelicious: 1995-1998|http://www.palewire.com/scrape/albums/covers/jaydeelicious.jpg
2007|4|Lindstrom and Prins Thomas|BBC Essential Mix|http://www.palewire.com/scrape/albums/covers/lindstrom%20prins%20thomas.jpg
2007|3|Go Home Productions|This Was Pop|http://www.palewire.com/scrape/albums/covers/this%20was%20pop.jpg
2007|2|Apparat|Walls|http://www.palewire.com/scrape/albums/covers/walls.jpg
2007|1|Caribou|Andorra|http://www.palewire.com/scrape/albums/covers/andorra.jpg
2006|10|Lily Allen|Alright, Still|http://www.palewire.com/scrape/albums/covers/alright%20still.jpg
2006|9|Nouvelle Vague|Nouvelle Vague|http://www.palewire.com/scrape/albums/covers/nouvelle%20vague.jpg
2006|8|Bookashade|Movements|http://www.palewire.com/scrape/albums/covers/movements.jpg
2006|7|Charlotte Gainsbourg|5:55|http://www.palewire.com/scrape/albums/covers/555.jpg
2006|6|The Drive-By Truckers|The Blessing and the Curse|http://www.palewire.com/scrape/albums/covers/blessing%20and%20curse.jpg
2006|5|Basement Jaxx|Crazy Itch Radio|http://www.palewire.com/scrape/albums/covers/crazy%20itch%20radio.jpg
2006|4|Love is All|Nine Times The Same Song|http://www.palewire.com/scrape/albums/covers/nine%20times.jpg
2006|3|Ewan Pearson|Sci.Fi.Hi.Fi_01|http://www.palewire.com/scrape/albums/covers/sci%20fi%20hi%20fi.jpg
2006|2|Neko Case|Fox Confessor Brings The Flood|http://www.palewire.com/scrape/albums/covers/fox%20confessor.jpg
2006|1|Ellen Allien & Apparat|Orchestra of Bubbles|http://www.palewire.com/scrape/albums/covers/orchestra%20of%20bubbles.jpg</pre>



<p>Now all that's left on our checklist is to figure out a way to download the cover art in addition to recording the urls. When we're interested in just snatching a simple file off the web, I like to use the urlretrieve() function found in Python's urlib module. All you have to do is add it to your import line, as below, and tell it where to save the files. I just stuff it in the extract loop so it pulls down the file immediately after scraping its row in the table. Check it out.</p>



<pre lang="Python">#!/usr/bin/env python
from mechanize import Browser
from BeautifulSoup import BeautifulSoup
import urllib, os

def extract(soup, year):
    table = soup.find("table", border=1)
    for row in table.findAll('tr')[1:]:
        col = row.findAll('td')
        rank = col[0].string
        artist = col[1].string
        album = col[2].string
        cover_link = col[3].img['src']
        record = (str(year), rank, artist, album, cover_link)
        print >> outfile, "|".join(record)
        save_as = os.path.join("./", album + ".jpg")
        urllib.urlretrieve("http://www.palewire.com" + cover_link, save_as)
        print "Downloaded %s album cover" % album

outfile = open("albums.txt", "w")
mech = Browser()
url = "http://www.palewire.com/scrape/albums/2007.html"
page1 = mech.open(url)
html1 = page1.read()
soup1 = BeautifulSoup(html1)
extract(soup1, 2007)
page2 = mech.follow_link(text_regex="Next")
html2 = page2.read()
soup2 = BeautifulSoup(html2)
extract(soup2, 2006)
outfile.close()</pre>

<p>While I was at it, I also added in an outfile where the scrape results are saved in a text file, just like we did in our previous recipes. Run this version and then check out your working directory, where you should see all the images as well as the new outfile.</p>



<p>Voila. I think we're done. If this is useful for people, next time we can cover how you leverage these basic tools against search forms and larger result sets. Per usual, if you spot a screw up, or I'm not being clear, just shoot me an email or drop a comment and we'll sort it out. Hope this is helpful to somebody.</p>



<p>And, as a postscript, since we're kind of on a roll here, I thought it might be fun to cook up an LAT version of the <a href="http://www.oreilly.com/catalog/pythoncook/">Python Cookbook</a> cover, in the classic O'Reilly style. What do you think? I couldn't quite find the right font.</p>



<img src="http://www.palewire.com/images/oreilly_lat.gif" alt="The Reporter's Python Cookbook" border=1/>