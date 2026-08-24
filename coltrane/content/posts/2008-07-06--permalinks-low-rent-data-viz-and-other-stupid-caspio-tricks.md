---
title: Permalinks, low-rent data viz and other stupid Caspio tricks
slug: permalinks-low-rent-data-viz-and-other-stupid-caspio-tricks
published_at: '2008-07-06T20:20:33-07:00'
wordpress_id: 134
---
<p>Today marked the release of <a href="http://www.latimes.com/news/local/la-me-charity6-2008jul06,0,6668563.story">a new Times investigation</a> into the poor performance of for-profit fundraisers hired by not-for-profit charities. The poster child is Citizens Against Government Waste (CAGW), an advocacy group that <a href="http://www.cagw.org/site/PageServer?pagename=about_Mission_History">rails against reckless government spending</a>.</p>



<p>According to reporting and analysis by Charles Piller and Doug Smith:</p>



<blockquote>Records filed with the California attorney general's office show that over the last decade, for-profit fundraisers for [CAGW] kept more than 94 cents of every donated dollar.</blockquote>



<p>And the bigger picture:</p>



<blockquote>In more than 5,800 campaigns on behalf of charities that were registered with the state attorney general from 1997 to 2006, the fundraisers reported taking in $2.6 billion. They kept nearly $1.4 billion -- about 54 cents of every dollar raised.</blockquote>



<p>As part of our effort to package the story for the Web, I worked with <em>Times</em> staff to publish all of the records collected for analysis as an online database. What we came up with allows readers to look up the track record of individual charities, browse charities of similar types, and quickly seek out the most and least efficient charities using a goofball visualization I cooked up with our graphics guy, <a href="http://www.studioburbank.com/">Thomas Lauder</a>. You can check it out <a href="http://www.latimes.com/news/local/la-charity-search-home,0,7128706.htmlstory">here</a>.</p>



<p>The app was pulled together using <a href="http://www.caspio.com/">Caspio</a>, a browser-based program for building data-driven web applications. While it is technically true, as the site claims, that developing a working Caspio app requires "no more programming," my experience has been that you're going to have to invest a significant amount of time hacking at its kludgey GUI to come up with something half-way decent. Whether you want to invest your time doing that, or mastering a more robust development option, is entirely up to you.</p>



<p><a href="http://www.tubotu.com/?p=43">Other</a>, <a href="http://blog.thescoop.org/archives/2008/06/29/caspios-lessons/">smarter</a> <a href="http://blog.thescoop.org/archives/2007/12/07/trial-by-caspio/">people</a> have invested a goodly amount of space to explaining Caspio's deficiencies, so I'll leave that to <a href="http://commonsensej.blogspot.com/2007/10/caspio-dustup.html">the</a> <a href="http://www.jacobian.org/writing/2007/sep/12/db-journalism/">links</a>. Instead let's break out below a couple tricks that helped me at least marginally improve today's product, in hopes they might be useful to somebody. (Though I suppose any "improvement" is a matter of opinion! Let me know what I fucked up.)</p>



<h2>Hack 01: Roll your own forms</h2>



<p>Caspio offers several templates. The one I use most often is the "search-and-result" set. It accepts a user's input and returns any matching values. Might sound complicated, but it's the same thing as Google. You pop something in, and you get back any hits. You can examine specimens in the wild <a href="http://dunes.cincinnati.com/data/crime/fbi/">here</a>, <a href="http://www.tbo.com/news/reports/foreclosures/">here</a> and <a href="http://www.azcentral.com/news/datacenter/babynames.html">here</a>. (Thorough readers will notice that, at least at the time of writing, the Cincinnati app is dead on arrival, bearing only the cryptic message "<a href="http://www.palewire.com/images/dead-caspio-cropped.png">DataPage does not exist. (Caspio Bridge error) (50501)</a>.")</p>



<p>Since the "search" and "result" sides of the app are glued together in a single panel, the search box can't be very easily plugged in around your site. You'll have to find a way to make Caspio's gunky JavaScript code work in each and every location where you want to encourage user input. The result is that most Caspio apps -- including all three linked above -- tend to live in backwater, standalone pages, lampooned by Matt Waite as "<a href="http://www.mattwaite.com/2008/01/02/data-ghettos/">data ghettos</a>." (Personally, I prefer "<a href="http://www.youtube.com/watch?v=SJ4EVnAxHIc">Ghettos of the Mind</a>.")</p>



<p>That might be acceptable if you're looking to make a destination page for your corporate intranet, like an employee directory. But it's just not good enough for news Web sites, which draw a huge share of their incoming traffic on the homepage and the first page of featured stories. If your database isn't prominently displayed there -- and it isn't unless you've got a search box or other entry point gaping open on the page -- you've losing a whole lot of potential traffic. I think there's something to be said for a "data central" section, but you're probably giving up a lot of clicks if you're waiting for people to hit the vague looking "data" link in your left-nav bar.</p>



<p>So what's the hack? It's pretty simple. Just build a search-and-result box without a search, which you then provide with your own custom HTML. You can then reuse the search box anywhere you want: the frontpage, right-rail, story-level reefer or -- heaven forfend -- standalone "data ghetto."</p>



<p>Here's how you do it, shot by shot.</p>



<img src="http://www.palewire.com/images/form-step1.png" alt="" />



<p>First turn on the advanced options and allow parameters.</p>



<img src="http://www.palewire.com/images/form-step2.png" alt="" />



<p>Tell Caspio it should look for an external parameter in the URL, rather than use it's native search form.</p>



<img src="http://www.palewire.com/images/form-step3.png" alt="" />



<p>Tell it which field it should run the inputs against. In this case, we're building a search on a data table's "name" field.</p>



<img src="http://www.palewire.com/images/form-step4a.png" alt="" />



<p>Now instruct Caspio to look for the user input after a query string variable called "name," and to evaluate it against the data table using "contains" style matching, as opposed to "exact" or "starts with" matching. If you were using a unique identifer like a primary key for the lookup (as you likely would if you were building a dropdown menu rather than a search box), you would probably want to use an "exact" match instead of "contains."</p>



<img src="http://www.palewire.com/images/form-step4b.png" alt="" />



<p>Then finish up by telling Caspio how to handle what to do with blank variables or circumstances where you don't have a match.</p>



<p>Now you should deploy the Caspio app as you normally would, and then craft an HTML form on a different page that points to its location, placing the user's input in the query string. For example, the search box in our charity app looks like this, with all the styling removed:</p>



<pre lang="HTML"><form action="http://www.latimes.com/news/local/la-charity-search-name,0,5949050.htmlstory" method="get">

<input maxlength="100" name="name" size="6" type="text" />

<input type="submit" value="Go" />

</form>

</pre>



<p>That'll send people to the following link, where they'll see the search results as they're formatted by the Caspio GUI.</p>



<pre lang="HTML">http://www.latimes.com/news/local/la-charity-search-name,0,5949050.htmlstory?name=Red Cross</pre>



<h2>Hack 02: Permalinks for easy deep linking</h2>



<p>An added benefit of using Hack 01 is that your results pages can have permalinks, albeit long and ugly ones. The link above will always call up the results for a search of "Red Cross," and if you build all your drilldown pages this way, using a primary key as the external parameter, they'll each have a distinct URL. That came in handy with the charity story because it allowed me to deep link charity names and types from <a href="http://http://www.latimes.com/news/local/la-me-charity6-2008jul06,0,6668563.story">the story</a> down into the database (ex. <a href="http://www.latimes.com/news/local/la-charity-search-detail,0,922401.htmlstory?CharityCode=713">Citizens Against Government Waste</a> and <a href="http://www.latimes.com/news/local/la-charity-search-type,0,4633762.htmlstory?TypeCode=18">disaster relief</a>)</p>



<h2>Hack 03: Low-rent data visualization as a novel entry point</h2>



<p>Once you set up the query string, there's no reason that your custom entry point must be an HTML form. My editors wanted to group the charities by their fundraising efficiency and give readers the chance to look at them group by group (i.e. which are the best, average, worst, <em>et cetera</em>.) We could have made a dropdown box, ordered list or sortable table. But the idea Thomas Lauder and I hatched instead was an interactive grid modeled on the <a href="http://mutualfunds.about.com/od/mutualfunds101/fr/stylebox.htm">Morningstar Style Box</a> that sorts charities by the size and efficiency of their fundraising efforts. I built it with <a href="http://www.alistapart.com/articles/imagemap">an old A List Apart trick</a> so that each square links to the list of charities in its category. Take a look at it <a href="http://www.latimes.com/news/local/la-charity-search-home,0,7128706.htmlstory">here</a>. We also made a smaller version, currently on the site's frontpage and in a story-level reefer. Here's a hideous screenshot to prove it. You'll have to go to <a href="http://www.latimes.com/news/local/la-me-charity6-2008jul06,0,6668563.story">the site</a> if you actually want to play with it.</p>



<img src="http://www.palewire.com/images/mini-grid.png" alt="" />



<p>Alright, I've got a few more up my sleeve, but that's probably enough for now. Per usual, far be it from me to say that these methods are the only or most efficient way to solutions. They're just the ones I got done on deadline. Feel free to tell me where I screwed up, or how I can do it better next time.</p>