---
title: 'Python Recipe: Read file, find pattern, print matches'
slug: python-recipe-read-a-file-search-for-a-pattern-print-your-matches
published_at: '2008-04-14T22:52:41-07:00'
wordpress_id: 100
---
<p>Our <a href="http://www.palewire.com/2008/04/05/python-recipe-open-a-file-read-through-it-print-each-line-matching-a-search-term/">first</a> <a href="http://www.palewire.com/2008/04/07/python-recipe-open-multiple-files-search-for-matches-count-your-hits-on-the-fly/">two</a> recipes focused primarily on how to open one or more files and loop through them line by line. While we paid a little attention to how we could search for patterns using <a href="http://www.amk.ca/python/howto/regex/regex.html#SECTION000310000000000000000">regular expressions</a>, we didn't try to do a whole lot with what we caught. Hell, we didn't even try very hard to write a good regex.</p>



<p>But when you start to get serious about searching for patterns in text, one of the obvious goals is to single out and collect your matches. Maybe you want to pull all the phone numbers out of big blobs of text. Or email addresses. Or anything enclosed in quotation marks. Whatever.</p>



<p>Here's one way to try it.</p>



<p>But before we get going, let me just say that I'm going to assume you read the first couple recipes and won't be working too hard to explain the stuff covered there. And keep in mind that my keystrokes are coming right off my home computer, which runs <a href="http://www.ubuntu.com/">Ubuntu Linux</a>. I'll try to provide Mac and Windows translations as we go, but I might muck a phoneme here and there. If anything is screwed up and doesn't work on your end, just shoot me an email or drop a comment. We'll iron it out.</p>



<p>Formalities aside, here's the example task I've selected to achieve our mission.</p>



<ol>

	<li>Download the King James Version of the Holy Bible.</li>

	<li>Read through each line of text.</li>

	<li>Capture each four-letter word.</li>

	<li>Print them out.</li>

</ol>



<p>Let's do it.</p>



<h2>1. Open the command line, create a working directory, move there.</h2>



<p>We're going to start the same way we did in the first two lessons, creating a working folder for all our files and moving in with our command line. </p>



<pre lang="bash">cd Documents/
mkdir py-search-and-capture
cd py-search-and-capture/</pre>



<p>The commands should work just as easily in Mac as in Linux. If you're working in Windows, you'll be on the "C:/" file structure, rather than the Unix-style structure above. So you might"mkdir" a new working directory in your "C:/TEMP" folder or wherever else you'd like to work. Or just make a folder wherever through Windows Explorer and "cd" there after the fact through the command line.</p>



<h2>2. Download our source file, The King James Version of the Holy Bible</h2>



<p>We're going to use <a href="http://www.gutenberg.org/ebooks/10">the text file</a> provided Project Gutenberg as our source. As in the earlier lessons, I'm going to use the curl command-line utility to retrieve the file, but you should feel free to download it to our working directory using your web browser, if you prefer.</p>



<pre lang="bash">curl -O http://www.gutenberg.org/dirs/etext92/bible11.txt</pre>



<h2>3. Create our python script in the text editor of your choice.</h2>



<pre lang="bash">vim search.py</pre>



<p>The line above, which again should work for Linux or Mac, will open a new file in <a href="http://www.google.com/url?sa=t&ct=res&cd=1&url=http%3A%2F%2Fwww.vim.org%2F&ei=uzoESIj8LKnmpgTRy43VBw&usg=AFQjCNE8C6iOb5uQLy74YKg-WBd9hikKaw&sig2=vP2XqMTTDBFF49Gy22gxJQ">vim</a>, the command-line text editor that I prefer. You can follow along, or feel free to make your own file in the application you prefer. If you're a newbie Windows user, <a href="http://www.google.com/url?sa=t&ct=res&cd=1&url=http%3A%2F%2Fen.wikipedia.org%2Fwiki%2FNotepad&ei=zToESKWNL4uqpwT2k73dBw&usg=AFQjCNEXWgXDcow8vXjueJBIOmWghv1lhw&sig2=aDintKlEbbRHHWcaHXoz1w">Notepad</a> should work great.</p>



<p>If you're following along in vim, you'll need to enter "insert mode" so you can start entering text. Do that by hitting:</p>



<pre lang="bash">i</pre>



<h2>4. Write the code!</h2>



<pre lang="python">#!/usr/bin/env python
import re

bible = open("kjv10.txt", "r")
regex = re.compile(r'\b\w{4}\b')

for line in bible:
    four_letter_words = regex.findall(line)
    for word in four_letter_words:
        print word</pre>



<p>Our file opens by importing the re module, which will allow us to call upon Python's regular expression library. We then open our Bible into a variable of the same name and, as in previous recipes, open a loop that will iterate through each line in the file.</p>



<p>The new stuff comes next. The first statement above our loop uses re's compile method to store our regular expression pattern into a variable called "regex." (As commenter Paddy suggested <a href="http://www.palewire.com/2008/04/14/python-recipe-read-a-file-search-for-a-pattern-print-your-matches/#comment-73091">below</a>, it's a good idea to put it above the loop so it doesn't have to be repeated on each iteration.) Remember, our goal is to match any four-letter words. There are three regex symbols I squished together to give it a hack. They are defined as follows. I've drawn the definitions from <a href="http://www.amk.ca/python/howto/regex/regex.html#SECTION000310000000000000000">this</a> Python reference, which can probably help you crack most nuts.</p>



<ul>

	<li>\b - Word boundary. This is a zero-width assertion that matches only at the beginning or end of a word.</li>

	<li>\w - Matches any alphanumeric character</li>

	<li>{m,n} - There must be at least m repetitions, and at most n.</li>

</ul>



<p>So when you piece them together like so, "\b\w{4}\b", what you're asking for is any stretch of four alphanumeric characters between two word boundaries. Make sense?</p>



<p>Next, equipped with our regex, we create another variable called "four_letter_words." In it we see our regex variable pressed against a re method we haven't used before. In the previous lessons we used the kludgy match() function to make our hits. Here we're using something more elegant. It's findall(), which will return all the matches within our line as a list. And by connecting it to our pre-compiled "regex" variable, we're setting that as the pattern it should look for. </p>



<p>We can expect plenty of lines with more than one match, so we'll set up another loop to run through "four_letter_words" and print out all the hits. And then we're done. Save and quit out of your script (ESC, SHIFT+ZZ in vim) and fire it up from the command-line:</p>



<pre lang="bash">python py-search.py</pre>



<p>And, voila, there you have it. All the four-letter words in the KJV. Every f*cking one.</p>



<p>Unless I messed something up, of course. Per usual, if you spot a screw up, or I'm not being clear, just shoot me an email or drop a comment and we'll sort it out. Hope this is helpful to somebody.</p>