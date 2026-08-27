---
title: 'Python recipe: Connect to MySQL, query, print the results'
slug: python-recipe-connect-to-mysql-database-execute-a-query-print-the-results
published_at: '2008-04-26T10:28:57-07:00'
wordpress_id: 112
---
<p>Today let's take a look at how you can use Python to connect to your MySQL database, issue a SQL query and do things with the results.</p>

<p>It's not that hard to write a simple SQL command by hand and muck with the results, so why bother? Like earlier recipes, our reward will be saving time and energy by automating a task that would normally require manual labor. It becomes clear when you bump into something you need to do 500 times, or make part of your daily routine.</p>

<p>For example, one thing I try to do at work is keep documentation related to all of my datasets. I keep a series of wiki pages devoted to each database that lists its data sources, explains its origins, catalogs helpful SQL snippets and defines the fields in each table.</p>

<p>The wiki application I use -- <a href="http://twiki.org/">TWiki</a> -- accepts HTML code and the convention I've settled on is to format each table's field definitions in a standard set of <a href="http://www.w3schools.com/tags/tag_table.asp">table tags</a>. So every time I add a new MySQL table and want to document it, I need to build another HTML table for the wiki. That's a pain to do by hand, especially when the table has a lot of fields. To save Ben the trouble, let's write a simple Python script that will...</p>

<ol>
	<li>Log into the MySQL database</li>
	<li>Acquire the list of columns from a MySQL table</li>
	<li>Print the columns out in an HTML table</li>
</ol>

<p>It's not very exciting, but it'll introduce you to the basics. And once you start walking you'll quickly be able to run.</p>

<h2>1. Install the MySQLdb module.</h2>

<p>Before you can tap into your MySQL db with Python, you need to install the "MySQL for Python" module (a.k.a. MySQLdb). The file is found <a href="http://sourceforge.net/projects/mysql-python/">here</a>, and, while I haven't tested it, it looks like there's a .exe installer for you Windows kids. There's also a nice stab and cataloging different methods <a href="http://docs.turbogears.org/1.0/DatabaseMySQL">here</a>. If, like me, you're running Ubuntu Linux, installation is as simple as opening GNOME's package manager and selecting the "python-mysqldb" package, or running an "apt-get" from your terminal.</p>

<p>You can test whether its been properly installed by opening up your python shell and trying to import the module. So fire up the shell...</p>

<pre lang="Bash">python</pre>

<p>...and pop it off...</p>

<pre lang="Python">Python 2.5.1 (r251:54863, Mar  7 2008, 04:10:12)
[GCC 4.1.3 20070929 (prerelease) (Ubuntu 4.1.2-16ubuntu2)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import MySQLdb
>>> </pre>

<p>If the interpreter accepts the commands and kicks down the next line without an error, you know you're okay. If it throws an error, you know something is off.</p>

<h2>2. Open the command line, create a working directory, move there.</h2>

<p>Before we get going, let me just say that I'm going to assume you read the first couple recipes and won't be working too hard to explain the stuff covered there. And keep in mind that my keystrokes are coming right off my home computer, which runs Ubuntu Linux. I'll try to provide Mac and Windows translations as we go, but I might muck a phoneme here and there. If anything is screwed up and doesn't work on your end, just shoot me an email or drop a comment. We'll iron it out.</p>

<p>We're going to start the same way we did in the first lessons, creating a working folder for all our files and moving in with our command line.</p>

<pre lang="Python">cd Documents/
mkdir py-connect-to-mysql
cd py-connect-to-mysql/</pre>

<p>The commands should work just as easily in Mac as in Linux. If you're working in Windows, you'll be on the C:/ file structure, rather than the Unix-style structure above. So you might mkdir a new working directory in your C:/TEMP folder or wherever else you'd like to work. Or just make a folder wherever through Windows Explorer and cd there after the fact through the command line.</p>

<h2>3. Create our python script in the text editor of your choice.</h2>

<pre lang="Bash">vim py-connect-to-mysql.py</pre>

<p>The line above, which again should work for Linux or Mac, will open a new file in <a href="http://www.google.com/url?sa=t&amp;ct=res&amp;cd=1&amp;url=http%3A%2F%2Fwww.vim.org%2F&amp;ei=uzoESIj8LKnmpgTRy43VBw&amp;usg=AFQjCNE8C6iOb5uQLy74YKg-WBd9hikKaw&amp;sig2=vP2XqMTTDBFF49Gy22gxJQ">vim</a>, the command-line text editor that I prefer. You can follow along, or feel free to make your own file in the application you prefer. If you're a newbie Windows user, <a href="http://www.google.com/url?sa=t&amp;ct=res&amp;cd=1&amp;url=http%3A%2F%2Fen.wikipedia.org%2Fwiki%2FNotepad&amp;ei=zToESKWNL4uqpwT2k73dBw&amp;usg=AFQjCNEXWgXDcow8vXjueJBIOmWghv1lhw&amp;sig2=aDintKlEbbRHHWcaHXoz1w">Notepad</a> should work great.</p>

<p>If you're following along in vim, you'll need to enter "insert mode" so you can start entering text. Do that by hitting:</p>

<pre lang="Bash">i</pre>

<h2>4. Write the code!</h2>

<pre lang="Python" line="1">#!/usr/bin/env python
import sys, MySQLdb

def PrintFields(database, table):
    """ Connects to the table specified by the user and prints out its fields in HTML format used by Ben's wiki. """
    host = 'localhost'
    user = 'user'
    password = 'password'
    conn = MySQLdb.Connection(db=database, host=host, user=user, passwd=password)
    mysql = conn.cursor()
    sql = """ SHOW COLUMNS FROM %s """ % table
    mysql.execute(sql)
    fields=mysql.fetchall()
    print '<table border="0"><tr><th>order</th><th>name</th><th>type</th><th>description</th></tr>'
    print '<tbody>'
    counter = 0
    for field in fields:
        counter = counter + 1
        name = field[0]
        type = field[1]
        print '<tr><td>' + str(counter) + '</td><td>' + name + '</td><td>' + type + '</td><td></td></tr>'
    print '</tbody>'
    print '</table>'
    mysql.close()
    conn.close()

users_database = sys.argv[1]
users_table = sys.argv[2]
print "Wikified HTML for " + users_database + "." + users_table
print "========================"
PrintFields(users_database, users_table)</pre>

<p>Obviously, the first thing you need to do is import the modules we need. The <a href="http://docs.python.org/lib/module-sys.html">"sys" module</a> will allow us to accept inputs from the command line later, and our new friend, MySQLdb, will help us connect to the database. </p>

<p>Then you can see that the bulk of the script is taken up by a function, named PrintFields, that extends from line four to line 32. That contains all of the card tricks we'll need to connect to our local db, run a query and print it out however we want. In this case, we're spitting out the data in an HTML shell I've concocted to create a complete table when it's all done. </p>

<p>After the loop closes at line 32, the remainder of the script uses sys to grab the first two arguments passed in by the user and hand them over to the function. So this way, by providing the database and table names at the time of execution, I can ask the script to print out the fields from any table I've got. For instance, we can print out the generic time_zone table that comes MySQL's "mysql" settings database like so...</p>

<pre lang="Bash">python py-connect-to-mysql.py mysql time_zone</pre>

<p>And you should get something like ...</p>

<pre lang="Bash">Wikified HTML for mysql.time_zone
========================
<table border="0"><tr><th>order</th><th>name</th><th>type</th><th>description</th></tr>
<tbody>
<tr><td>1</td><td>Time_zone_id</td><td>int(10) unsigned</td><td></td></tr>
<tr><td>2</td><td>Use_leap_seconds</td><td>enum('Y','N')</td><td></td></tr>
</tbody>
</table></pre>

<p>Then what I'd normally do is just copy and paste that into my wiki. The script doesn't have any error handling or fancy tricks, which I think makes it a good starter example on the basics. Let's pull out the things you'll need to know. So let's walk through a few of them.</p>

<pre lang="Python" line="7">
    host = 'localhost'
    user = 'user'
    password = 'password'
</pre>

<p>This first snippet contains all the local information about your MySQL that will need to be customized to fit your rig. You'll need to change the definitions for user and password to whatever it is you use. And if the database you want to tap isn't on your localhost, but perhaps networked elsewhere, you'll need to change the host definition to its IP address or alias.</p>

<pre lang="Python" line="10">
    conn = MySQLdb.Connection(db=database, host=host, user=user, passwd=password)
    mysql = conn.cursor()
</pre>

<p>Then this next step will pass all of your local specifics to MySQLdb and open up a "cursor." You can use that to interact with the database in the same way you normally would with Microsoft Access or another piece of <a href="http://en.wikipedia.org/wiki/Graphical_user_interface">GUI software</a>. A lot of people might name the variable containing the cursor as "cursor," but it really doesn't matter. As seen above, I like to name it mysql. It's just personal preference. Notice that we didn't define the database variable in the earlier snippet. That's because it's being passed into the function by the user. We know that because it's up there at the top of our function...</p>

<pre lang="Python" line="4">def PrintFields(database, table):</pre>

<p>...and fed in at the bottom after we capture the user input with sys...</p>

<pre lang="Python" line="34">users_database = sys.argv[1]</pre>

<p>...and then passed in with our function call...</p>

<pre lang="Python" line="38">PrintFields(users_database, users_table)</pre>

<p>But what the hell is in that argv variable, anyway? Let's find out. I'm going to edit our script to include the following line...</p>

<pre lang="Python">print sys.argv</pre>

<p>...run the script again...</p>

<pre lang="Bash">python py-connect-to-mysql.py mysql time_zone</pre>

<p>...and here's what we get...</p>

<pre lang="Bash">['py-connect-to-mysql.py', 'mysql', 'time_zone']</pre></pre>

<p>Pretty self-explanatory, right? Now back to our function.</p>

<pre lang="Python" line="13">
    sql = " SHOW COLUMNS FROM %s " % table
    mysql.execute(sql)
</pre>



<p>With our connection set, the next thing to do is to use MySQL to run a query. I do it by storing a SQL command in a variable and then passing it to to MySQLdb execute function. You'll note that I use Python's magic "%s" command to write in the contents of the table variable, which, like the database variable, has been passed into the function by the user. By doing that, we're now able to run that same SHOW COLUMNS command on whatever database and table combination we pass in. Provided the table actually exists. </p>



<p>It's simple tricks like that which will enable you to really start flying with automation. What if your job required you to kick out data reports for each or any of the 50 states on command, or if you wanted to automate a web scrape to deposit its findings in your database every time it runs, or maybe even make an RSS feed that updates every 15 minutes. A simple concept like this, which allows for some of the SQL specifics to be specified programmatically, could save you a ton of time.</p>



<pre lang="Python" line="16">   fields=mysql.fetchall()</pre>



<p>This next line will store the results of the query in a variable called fields, which we'll print out using one of the simple loops I covered in <a href="http://www.palewire.com/2008/04/05/python-recipe-open-a-file-read-through-it-print-each-line-matching-a-search-term/">previous recipes</a>, pulling out the first and second fields (name and datatype) for my table. You could take a look what's in the list by printing it out to your terminal before running the loop. Let's try that by adding...</p>



<pre lang="Python">print fields</pre>



<p>...to our script. Run it again from the top and now you'll get the ...</p>



<pre lang="Bash">(('Time_zone_id', 'int(10) unsigned', 'NO', 'PRI', None, 'auto_increment'), ('Use_leap_seconds', "enum('Y','N')", 'NO', '', 'N', ''))</pre>



<p>Since I don't want all of the settings for my docs, just the name and field type, as we loop through each row I only pull out the first two items (field[0], field[1]). All the rest of the mess around there is designed to print out the data in my custom HTML shell, which really shouldn't matter for your purposes, so why bother here. So, what the hell, I think we're done. Per usual, if you spot a screw up, or I'm not being clear, just shoot me an email or drop a comment and we'll sort it out. Hope this is helpful to somebody.</p>