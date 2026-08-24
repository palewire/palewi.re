---
title: 'Python Recipe: Open a file, read it, print matching lines'
slug: python-recipe-open-a-file-read-through-it-print-each-line-matching-a-search-term
published_at: '2008-04-05T08:49:58-07:00'
wordpress_id: 93
---
<p>A couple of friends out there are valiantly teaching themselves the <a href="http://www.google.com/url?sa=t&amp;ct=res&amp;cd=3&amp;url=http%3A%2F%2Fen.wikipedia.org%2Fwiki%2FPython_(programming_language)&amp;ei=dYn3R_GUHYyKpwTA2uSCAQ&amp;usg=AFQjCNH9Zj5BO1JqfEoXtYHusciWciPhyw&amp;sig2=wUObhPmolLlcHaWLfM2jIQ">Python</a> programming language in their free time. Who are they? Hack reporters like me, picking up computer skills in a continuing quest to better sift, organize and analyze information. And, in the process, maybe keep our jobs.</p>



<p>There are <a href="http://www.google.com/url?sa=t&amp;ct=res&amp;cd=1&amp;url=http%3A%2F%2Fwww.diveintopython.org%2F&amp;ei=soD3R9zRI4_SpgSlvrGXAQ&amp;usg=AFQjCNGQNAs7-XfPQXeZePlQKHmTA13dJQ&amp;sig2=STTYEjUUr__P0LCYzugcqA">a</a> <a href="http://www.greenteapress.com/thinkpython/">couple</a> great books available free online but it's pretty tough to start stringing all the fundamentals into a problem-solving script all on your own. So why not write up some simple recipes that attack problems common to our particular tribe?</p>



<p>One of the ways computer programming can be of great use to a reporter is as a text parser. We all have more documents than we have time.  So a common challenge is training your computer to read through a big blob of text and return any hits on terms you're interested in (i.e. the name of the mayor, a popular pesticide, a roster of local police officers).</p>



<p>If it's a one-off effort, you can probably get this done quickly using search tools included in common quality text editors (ex. <a href="http://www.ultraedit.com/">Ultraedit,</a> <a href="http://notepad-plus.sourceforge.net/uk/site.htm">Notepad++</a>, <a href="http://macromates.com/">TextMate</a>). But if you've got a steady stream of files, like a weekly dump of court filings, or a really big bad file, sometimes it's preferable to train your computer to do the work for you.</p>



<p>In that spirit, the following instructions are designed to show you how to use Python to search through a text file (The Sonnets of William Shakespeare), find any lines that contain our sample search term ("love"), and then print out the hits into a new file we can keep as a memento.</p>



<p>We'll be dealing with a source file that's probably cleaner than most documents you'll get from the government, and certainly a lot tidier than anything you've converted from a PDF file using an <a href="http://www.google.com/url?sa=t&amp;ct=res&amp;cd=2&amp;url=http%3A%2F%2Fen.wikipedia.org%2Fwiki%2FOCR&amp;ei=Don3R6TqA5OkpwTwr-B-&amp;usg=AFQjCNHMFPblFGTHSM76WDSX2SkNbxkqaQ&amp;sig2=uwlPh0CUVchwL5Hp_rDZ4Q">OCR</a> application, but if you're a totally newbie, my hope is that this can help you get a grip on how the hell all the pieces described in the textbooks fit together into something almost useful.</p>



<p>Since I'm now a full-time geek, I do most of my work on computers that run some flavor of Linux. The step-by-step instructions that follow will walk you through each keystroke on the command line in <a href="http://www.google.com/url?sa=t&amp;ct=res&amp;cd=3&amp;url=http%3A%2F%2Fen.wikipedia.org%2Fwiki%2FUbuntu_(Linux_distribution)&amp;ei=t4j3R8z6IKi-pgSXhtF3&amp;usg=AFQjCNEm1W3O1_OsDnkAl5emlxHmgPxPAQ&amp;sig2=f8zSJLp9T0AquKr-oWMTPg">Ubuntu</a>, which is what I run at home. But since most people who might be interested in this are probably running Windows XP or Mac OS X, I'll try to include translations as we go.</p>



<p>The one prerequsite for the whole endeavor is that you already have a working installation of Python. If you're working in Windows and you don't, I'd recommend visiting <a href="http://www.activestate.com/Products/activepython/">ActiveState</a> and downloading the installer for their ActivePython distribution. If you're rocking a Macbook, you can find out whether you're rolling with Python by opening your terminal and entering the following:</p>



<pre lang="Bash">which python</pre>



<p>If you've got it properly installed, it should return something like</p>



<pre lang="Bash">/usr/bin/python</pre>



<p>If it's not working out, I'd recommend <a href="http://www.diveintopython.org/installing_python/index.html">the installation instructions</a> in Mark Pilgrim's excellent book, Dive Into Python.</p>



<p>Alright, with all that out of the way, let's get to the recipe.</p>



<h2>1. Open the command line, create a working directory, move there.</h2>



<pre lang="Bash">cd $HOME
mkdir Documents/py-search
cd Documents/py-search</pre>



<p>The three commands above, which should work just as easily in Mac as in Linux, will move us to our home directory, create a new subdirectory in your Documents folder, and relocate to the new folder.</p>



<p>If you're working in Windows, you'll be on the "C:/" file structure, rather than the Unix-style structure above. So you might "mkdir" a new working directory in your "C:/TEMP" folder or wherever else you'd like to work. Or just make a folder wherever through Windows Explorer and "cd" there after the fact through the command line.</p>



<h2>2. Download our source file, The Sonnets of William Shakespeare.</h2>



<pre lang="Bash">curl -O http://www.gutenberg.org/dirs/etext97/wssnt10.txt</pre>



<p>The line above uses the curl command line utility to download a copy of Shakespeare's work from the <a href="http://www.google.com/url?sa=t&amp;ct=res&amp;cd=1&amp;url=http%3A%2F%2Fwww.gutenberg.org%2F&amp;ei=BI73R6_pPISmpwTs8qiGAQ&amp;usg=AFQjCNEwWvhQCQqfxd5f1CbKz4kDmWOgtw&amp;sig2=zRLSSO5_tlJUa4Q_YjXXRQ">Project Gutenberg</a> Web site. Mac users with curl installed should be able to issue the same command. Windows users, or anyone without curl, will probably be able to most easily snatch the file just by visiting <a href="http://www.gutenberg.org/dirs/etext97/wssnt10.txt">the link</a> in a web browser and saving the file to the working directory created in step one.</p>



<h2>3. Create our python script in the text editor of your choice.</h2>



<pre lang="Bash">vim py-search.py</pre>



<p>The line above, which again should work for Linux or Mac, will open a new file in <a href="http://www.google.com/url?sa=t&amp;ct=res&amp;cd=1&amp;url=http%3A%2F%2Fwww.vim.org%2F&amp;ei=fI_3R7rdEIHUpgTsleWSAQ&amp;usg=AFQjCNE8C6iOb5uQLy74YKg-WBd9hikKaw&amp;sig2=MmXWcI-I3tIW0vBQUWiXgA">vim</a>, the command-line text editor that I prefer. You can follow along, or feel free to make your own file in the application you prefer. If you're a newbie Windows user, <a href="http://en.wikipedia.org/wiki/Notepad">Notepad</a> should work great.</p>



<p>If you're following along in vim, you'll need to enter "insert mode" so you can start entering text.  Do that by hitting:</p>



<pre lang="Bash">i</pre>



<h2>4. Write the code!</h2>



<pre lang="Python" line="1" colla="+">#!/usr/bin/env python

import re

shakes = open("wssnt10.txt", "r")

for line in shakes:
    if re.match("(.*)(L|l)ove(.*)", line):
        print line,</pre>



<p>If, like my friends, you've been working through some common Python tutorials, I'm guessing a lot of that looks familar to you.</p>



<p>The first line is a <a href="http://en.wikipedia.org/wiki/Shebang_(Unix)">"shebang"</a> that, on execution of the file, instructs the computer to process the script using the python interpreter. The "import re" pulls in <a href="http://docs.python.org/lib/module-re.html">Python's standard regular expression module</a> so we can use it later to search the text. The open() command grabs the Shakespeare file we've just downloaded and opens it up. The "r" is for read mode.</p>



<p>The three staggered statements that follow are a loop that runs through each line in the document, as dictated by the first statement. The second statement uses <a href="http://www.google.com/url?sa=t&amp;ct=res&amp;cd=1&amp;url=http%3A%2F%2Fwww.regular-expressions.info%2Fpython.html&amp;ei=qJT3R9GRFabopASVx7yOAQ&amp;usg=AFQjCNHl7XwdC7m3xt26uu6oInBwYX1lOw&amp;sig2=SgkINQJUbkJB1FIERp8qmw">the re.match() function</a> we imported at the top to evaluate the latest line on each iteration through the loop by testing it against that scary looking mess in its first parameter.</p>



<p>So, what is that thing? "(.*)(L|l)ove(.*)", say what?</p>



<p>That's a regular expression I designed specifically to catch any instances of the search term I'm after.  If you're not familar with <a href="http://en.wikipedia.org/wiki/Regular_expression">regular expressions</a>, they're a powerful language for matching strings of text. When you first get started, they can be a bit intimidating, but once you learn a couple tricks, you'll quickly see how useful they can be. One of my favorite geek jokes is <a href="http://xkcd.com/208/">this cartoon</a> on the utility of a well-timed "regex"</p>



<p>So how does it work? There are two tricks to learn. Remember, our goal is to find any line in Shakespeare's sonnets that include the word love. But, when we think about it, we can't just search for "love" because our loop is evaluating the text line by line, not word by word. So if we just ask for "love," we'd only get lines that include <em>only</em> the word "love." Plus the word could appear in any number of common grammatical variations (ex. "Love," "lover," "lovesick," "self-love") that we'd also like to capture.</p>



<p>That's where the regular expressions come in. You'll notice that the expression is bracketed by two "(.*)" statements. In regular expression language, the "." command matches any string and the "*" repeats whatever command precedes it zero or more times, so together they will match any string of any length. When bracketed around a search term, like "love," it should return a match on a line of text regardless of where in the line "love" appears. In other words, it would match <a href="http://www.youtube.com/watch?v=cO9GB_KUAQI">"She loves you,"</a> <a href="http://www.youtube.com/watch?v=LLv_VaTGxH0">"love is a many spendored thing"</a> or <a href="http://www.youtube.com/watch?v=YzB-3oKIfRw">"ain't talking 'bout love."</a></p>



<p>But, all by itself "(.*)love(.*) wouldn't match <a href="http://www.youtube.com/watch?v=nrvNzH9aaUE">"America: What Time is Love?"</a> or  <a href="http://www.youtube.com/watch?v=50EALZU4D6A">"Love Is Only A Feeling."</a> Why not? Because those songs have an uppercase L and we're just asking for lowercase. Bummer, right?</p>



<p>One way to fix that would be to add an option that gives the regular expression variations on the term to look for. You can do that by adding another parenthesis set and separating the options with a "|" pipe. That's where the "(L|l)" above came from. Combine that with the (.*) commands and we should have a quick and dirty regex to catch the lines we're after. Though quick studies will catch a flaw in the design. As we'll see in our result set later, this sort of dragnet approach will also yield hits on things we might not want to catch, words like "glove" and "lovely" will match just as easily as "lovesick" or "lover." Feel free to tweak the statement and try to finetune your results. There's a ton more you can do with regular expressions than what I've described. So don't take my example too seriously. I just wanted to show off a couple of the most common regex commands.</p>



<h2>5. Save your script and run it.</h2>



<p>If you're working along with me in vim, you'll need to save your work before exiting. The easiest way to do that is to exit insert mode by hitting the ESC key and then hold SHIFT and hit the Z key twice in a row.  If you're working in your own text editor, just save it however you're comfortable.</p>



<p>Now jump back onto the command line resting in your working directory and tell python to fire that mother off.</p>



<pre lang="Bash">python py-search.py</pre>



<p>Voila. There they are, flying across your screen is every line in Shakespeare's sonnets containing the word love. And if you wanted to print them out to a new text file, rather than just dump them on the screen, jump back into your script and try something more like this.</p>



<pre lang="Python" line="1" colla="+">#!/usr/bin/env python
import re

shakes = open("wssnt10.txt", "r")
love = open("love.txt", "w")

for line in shakes:
    if re.match("(.*)(L|l)ove(.*)", line):
        print >> love, line,</pre>



<p>Now just open love.txt and you should find the same results as before.</p>



<p>The only difference in this script is that we're now opening an outfile called love (notice that it's "w" mode, for write, rather than "r" mode like the source) and modifying our print line to kick the results there, instead of the console.</p>



<p>That's all folks. Per usual, if I've screwed something up, or I'm not being clear, just shoot me an email or drop a comment and we'll sort it out. Hope this is helpful to somebody.</p>