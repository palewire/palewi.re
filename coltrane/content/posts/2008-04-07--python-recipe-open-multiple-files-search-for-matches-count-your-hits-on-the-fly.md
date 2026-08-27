---
title: 'Python recipe: open files, find matches, count hits'
slug: python-recipe-open-multiple-files-search-for-matches-count-your-hits-on-the-fly
published_at: '2008-04-07T01:06:45-07:00'
wordpress_id: 95
---
<p>I got some feedback from our beginners on the <a href="http://www.palewire.com/2008/04/05/python-recipe-open-a-file-read-through-it-print-each-line-matching-a-search-term/">Python recipe</a> I put up yesterday. They had a couple good questions about ways they can branch off, which I think we can cover pretty quick in another post.</p>



<p>To recap, Saturday's script opened a single file (Shakespeare's sonnets), searched the text line by line for a search term ("love") using a basic regular expression, and  then closed by printing the hits to a new text file. Today's recipe will do all that, and a couple other things that might be helpful.</p>



<p>For reason's discussed in my previous post, I think munching through text with Python is going to be most useful for a reporter when she can leverage its power against large bodies of text.  Our first example only operated on a single file. Out there in the real world, with deadlines, diets and kids to pick up at soccer practice, why should we invest the time learning to write a computer script to process a single file when we might be able to hack out the job with CTRL-F and just be done with it?</p>



<p>I feel that.</p>



<p>So, let's take the next step. Let's learn how to crack open a whole directory full of files and slam each one through our wood chipper.</p>



<p>But before we get going, let me just say that I'm going to assume you read <a href="http://www.palewire.com/2008/04/05/python-recipe-open-a-file-read-through-it-print-each-line-matching-a-search-term/">yesterday's recipe</a> and won't be working too hard to explain the stuff covered there. And keep in mind that my keystrokes are coming right off my home computer, which runs <a href="http://www.ubuntu.com/">Ubuntu Linux</a>. I'll try to provide Mac and Windows translations as we go, but I might muck a phoneme here and there. If anything is screwed up and doesn't work on your end, just shoot me an email or drop a comment. We'll iron it out.</p>



<p>Formalities aside, here the example task I've selected to achieve our mission.</p>



<ol>

	<li>Download the works of Friedrich Nietzsche.</li>

	<li>Train our computer to open the books one by one.</li>

	<li>Read through the text of each.</li>

	<li>Find all the lines that contain the german word for hate (<em>hasse</em>, <em>hasst</em>, <em>hassen</em>)</li>

	<li>Print out the hits.</li>

	<li>Count up the totals for each book and figure which one is the hatenest (<em>das meisten hassten!</em>).</li>

</ol>



<p>Sound good? Let's do it.</p>



<h2>1. Open the command line, create a working directory, move there.</h2>



<pre lang="Bash">cd $HOME/Documents
mkdir py-search-multiple-files
cd py-search-multiple-files/
mkdir nietzsche</pre>



<p>We're going to start the same way we did yesterday, creating a working folder for all our files and moving in with our command line. The only difference this time is that we're making an additional subdirectory to hold the source files we'll be searching.</p>



<p>The commands should work just as easily in Mac as in Linux. If you're working in Windows, you'll be on the "C:/" file structure, rather than the Unix-style structure above. So you might "mkdir" a new working directory in your "C:/TEMP" folder or wherever else you'd like to work. Or just make a folder wherever through Windows Explorer and "cd" there after the fact through the command line.</p>



<h2>2. Download our source files, the works of Friedrich Nietzsche.</h2>



<p>If you <a href="http://www.gutenberg.org/browse/authors/n#a779">visit Project Gutenberg</a>, you can find variety of Nietzsche's work available for download. For our purposes, we're going to take all of the books available there printed in the author's native tongue, German. We could point and click our way through the process -- visiting each book's profile page and downloading its text to our new nietzsche folder -- but if your aim is to become a big-time computer nerd, you might be interested in a command-line trick that can pull them all down with a single line of code.</p>



<p>Yesterday we used the curl utility to pull down our Shakespeare file. If you pulled that off, I'm sure you can easily imagine how it could be replicated with each of today's files, provided that you know the right urls to hit. And I'm guessing it might look something like this.</p>



<pre lang="Bash">curl -O http://www.gutenberg.org/dirs/etext05/7zara10.txt
curl -O http://www.gutenberg.org/dirs/etext05/7ecce10.txt
curl -O http://www.gutenberg.org/dirs/etext05/7gbrt10.txt
curl -O http://www.gutenberg.org/dirs/etext05/7gtzn10.txt
curl -O http://www.gutenberg.org/dirs/etext05/7jnst10.txt
curl -O http://www.gutenberg.org/dirs/etext05/7msch10.txt</pre>



<p>But, man, that hardly seems easier that clicking around, does it? Thankfully, one of the great things you pick up as you learn your way around the command line is that there's almost always a way to trim down a repetitive task into an elegant, simple string of code. Here's how those six separate curls can be combined.</p>



<pre lang="Bash">cd nietzsche

curl -O "http://www.gutenberg.org/dirs/etext05/7{zara,ecce,gbrt,gtzn,jnst,msch}10.txt"

cd ..</pre>



<p>Remember how we used the (L|l) option statement in our regular expression yesterday to match our search pattern to phrases containing either an upper or lowercase 'L'? We can do a similar thing here with curl, reducing the six urls to their common parts and providing a list of options between the {}'s where we plug each link's unique string. We just use "cd" to commute down to our subdirectory and back. For more details on how curl works, try typing in:</p>



<pre lang="Bash">curl --help</pre>



<p>or</p>



<pre lang="Bash">curl --man</pre>



<p>Each should include instructions on all other sorts of crazy tricks you can pull off. And if you have something in mind, don't forget to ask <a href="http://www.google.com/search?hl=en&amp;client=firefox-a&amp;rls=com.ubuntu%3Aen-US%3Aofficial&amp;hs=bH6&amp;q=curl+tricks+linux&amp;btnG=Search">our good friend Google</a>.</p>



<p>If you can't get curl to work on your system, but you still want to play along, just go ahead and download the Nietzsche files one by one through your web browser. As long as you put them in the subdirectory we named after him, the stuff that follows should still work just fine.</p>



<h2>3. Create our python script in the text editor of your choice.</h2>



<pre lang="Bash">vim search.py</pre>



<p>The line above, which again should work for Linux or Mac, will open a new file in <a onclick="javascript:pageTracker._trackPageview ('/outbound/www.google.com');" href="http://www.google.com/url?sa=t&amp;ct=res&amp;cd=1&amp;url=http%3A%2F%2Fwww.vim.org%2F&amp;ei=fI_3R7rdEIHUpgTsleWSAQ&amp;usg=AFQjCNE8C6iOb5uQLy74YKg-WBd9hikKaw&amp;sig2=MmXWcI-I3tIW0vBQUWiXgA">vim</a>, the command-line text editor that I prefer. You can follow along, or feel free to make your own file in the application you prefer. If you're a newbie Windows user, <a href="http://en.wikipedia.org/wiki/Notepad">Notepad</a> should work great.</p>



<p>If you're following along in vim, you'll need to enter "insert mode" so you can start entering text.  Do that by hitting:</p>



<pre lang="Bash">i</pre>



<h2>4. Write the code!</h2>



<pre lang="Python" line="1" colla="+">#!/usr/bin/env python
import re, os

path = "./nietzsche"
freddys_library = os.listdir(path)

for book in freddys_library:
    file = os.path.join(path, book)
    text = open(file, "r")
    for line in text:
        if re.match("(.*)(hasse|hasst)(.*)", line):
            print line,</pre>



<p>Here's what we'll start with. If you cover up the top part of the script with your hand, you'll see that the three statements at the end look almost identical to what we wrote in the first lesson. The script iterates through each line in a file (in this case dubbed "text"), seeks out a match using the same methods described in detail yesterday, and then finally prints out cases where we find a hit.</p>



<p>The only major difference is that we've replaced portions of yesterday's statement designed to seek out variations on the word "love" with another quick-fix regex designed to net the common German forms of the word hate (<em>hasse</em>, <em>hasst,</em> <em>hassen</em>).</p>



<p>And then we've got all that junk up there above it. What's going on there?</p>



<p>The first thing to notice is that we added another module to the import statement. In addition to the "re" module we're using to match regular expressions, we've also introduced the "<a href="http://docs.python.org/lib/module-os.html">os" module</a>. The os library hooks you up with a bunch of easy ways to pull in basic information about your operating system and file structure for use in Python. Our next two statements put it to use right away. First we store our nietzsche subdirectory in a variable called "path," which is then passed to the os function listdir(). That will return a list of all the files contained within the directory. Regardless of how few, or how many, are stuffed down in there, the filenames will now all be stored in our second variable, "freddys_library."</p>



<p>Our next step is to open up a loop that will iterate through each file name in "freddys_library." Since the function simply returns each file's name, not its path, we have to link the two before we can open the file. So the first step is another os function brought in to meld the two. Then we're free to open the file the same way we did yesterday, which leads the way to the search-and-print loop we're already familar with. And since it's stored within the loop stepping through each book's file, it will be repeated for every title before the script ends.</p>



<p>Now save and quit out of your script (ESC, SHIFT+ZZ in vim) and fire it up from the command-line...</p>



<pre lang="Bash" line="1" colla="+">python py-search.py</pre>



<p>...and, voila, you should now have every line in Nietzsche that contains the word hate flying by on your screen.</p>



<p>Now here's the next set of tricks.</p>



<pre lang="Python" line="1" colla="+">#!/usr/bin/env python
import re, os

path = "./nietzsche"
freddys_library = os.listdir(path)
hate = open("hate.txt", "w")

for book in freddys_library:
    file = os.path.join(path, book)
    text = open(file, "r")
    hit_count = 0
    for line in text:
        if re.match("(.*)(hasse|hasst)(.*)", line):
            hit_count = hit_count + 1
            print >>  hate, book + "|" + line,

    print book + " => " + str(hit_count)
    text.close()</pre>



<p>This second snippet is identical to our first draft, with a few additions. The simplest change is first, to create a new file ("hate.txt") where our matches are now printed. You'll notice that the print statement has also been modified to output the book's file name and a pipe-delimiter along with each hit on hate. So each line in your out file should be labeled with the source file where it was found.</p>



<p>The second change is to introduce a new "hit_count" variable designed to keep a running count of the matches found in each book and report back the results. Since it's enclosed within the outer loop, the first "hit_count = 0" variable will reset the number to nil on each book's iteration. And then the placement of "hit_count + 1" within the subsequent if statement will click the variable's total up one each time a match is made and the interpreter runs through that portion of the script. The final touch is to close each run through the loop by printing the book's file name along with the total number of hits found after all of the lines had been evaluated. The number is enclosed in a str() function so that it's converted from an integer into a string, which can be easily concatenated with other strings for our print statement.</p>



<p>When you run version two, it'll now print out the total number of hits for each book, looking something like this:</p>



<pre lang="Bash">7msch10.txt => 13
7zara10.txt => 34
7ecce10.txt => 2
7gtzn10.txt => 5
7gbrt10.txt => 2
7jnst10.txt => 4</pre>



<p>It works, but it's pretty ugly. How can you tell the different books apart without memorizing their file names? Good thing we can fix that too. Check out how.</p>



<pre lang="Python" line="1" colla="+">#!/usr/bin/env python
import re, os

title = {
    "7ecce10.txt": "Ecce homo, Wie man wird, was man",
    "7gtzn10.txt": "Gotzen-Dammerung",
    "7msch10.txt": "Menschliches, Allzumenschliches",
    "7gbrt10.txt": "Die Geburt der Tragodie",
    "7jnst10.txt": "Jenseits von Gut und Bose",
    "7zara10.txt": "Also sprach Zarathustra"
}

path = "./nietzsche"
freddys_library = os.listdir(path)
hate = open("hate.txt", "w")

for book in freddys_library:
    file = os.path.join(path, book)
    text = open(file, "r")
    hit_count = 0
    for line in text:
        if re.match("(.*)(hasse|hasst)(.*)", line):
            hit_count = hit_count + 1
            print >>  hate, title[book] + "|" + line,

    print title[book] + " => " + str(hit_count)
    text.close()</pre>



<p>After referring back to our text files to figure out which files contain which books, I made the Python "dictionary" at the top of this snippet. It pairs up the files with the titles for later reference, which happens easy peasy there at bottom when the loop's current "book" variable is run against the dictionary to return its title for our output.</p>



<p>Now if you save your changes and fire it off again, you should be getting something more like this:</p>



<pre lang="Bash">Menschliches, Allzumenschliches => 13
Also sprach Zarathustra => 34
Ecce homo, Wie man wird, was man => 2
Gotzen-Dammerung => 5
Die Geburt der Tragodie => 2
Jenseits von Gut und Bose => 4</pre>



<p>Much nicer, nein?</p>



<p>Alright. That's all for tonight. I hope this helps y'all kick the can a little further down the road. Per usual, if I've screwed something up, or I'm not being clear, just shoot me an email or drop a comment and we'll sort it out. Hope this is helpful to somebody.</p>