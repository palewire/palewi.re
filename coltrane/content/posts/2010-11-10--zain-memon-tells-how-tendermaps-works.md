---
title: 'Q&A: Zain Memon tells how Tendermaps works'
slug: zain-memon-tells-how-tendermaps-works
published_at: '2010-11-10T07:53:40-08:00'
---
<img style="width:600px; border:3px solid #E5E5E5" src="/media/img/tendermaps-hand-600x448.png">

<p>Last weekend, San Francisco developers converged at <a href="http://www.gaffta.org/2010/11/09/the-great-urban-hack-re-cap/">The Great Urban Hack</a> to crank out some civically-minded sites. The focus was on the city's famous <a href="http://en.wikipedia.org/wiki/Tenderloin,_San_Francisco">Tenderloin neighborhood</a>. (Don't know it? Think <a href="http://en.wikipedia.org/wiki/Stonewall_riots">Stonewall</a> or <a href="http://en.wikipedia.org/wiki/The_Maltese_Falcon_(novel)">The Maltese Falcon</a>.)

<p>The one that caught my eye was <a href="http://tendermaps.com/">Tendermaps</a>. It's an interactive map of the neighborhood, but it's not drawn by the city government or <a href="http://projects.latimes.com/mapping-la/neighborhoods/">self-appointed journalists</a>. No, it's a collage of boundaries and landmarks drawn&mdash; by hand, <a href="http://www.sharpie.com/">with Sharpies</a>&mdash;by people who live and work in the area. <a href="http://tendermaps.com/">Check it out</a>.</p>

<p>To learn how it got online, I conducted an email interview with one of the developers, <a href="http://twitter.com/zainy">Zain Memon</a>. Here's what he said.</p>

<div id="detailborderbumper" class="thin"></div>

<p>How did you get the Sharpie drawings onto an online map?  I see you wrote they were "scanned, and the handmade mark-ups extracted, georectified, and superimposed," but I'm hoping you can be specific (a.k.a geeky) about the process. How is each one of those steps accomplished?</p>

<blockquote><p>We used <a href="http://walking-papers.org/">walking-papers.org</a> to generate paper map prints of the tenderloin. We printed these out in grayscale and had people mark them up with colored sharpies. Here's <a href="http://c0848462.cdn.cloudfiles.rackspacecloud.com/d18e50bd35a8ebc5861ff309bccc064e.png">a picture</a> of one of them.</p>

<p>We scanned all of the maps into JPEGs and then used the <a href="http://www.pythonware.com/products/pil/">Python Imaging Library</a> to lift drawings off them. The coolest part was separating the drawings from the map itself &mdash; we basically checked each pixel's color, threw away the grayscale, and antialiased the rest.  By reading the <a href="http://en.wikipedia.org/wiki/QR_Code">QR code</a> in the bottom right corner, we gathered the bounding box of the map, and from there we could easily slice up the drawing into georectified tiles: one tile layer for each map.</p></blockquote>

<p>Is any of the python code available online?</p>

<blockquote><p>Not at the moment, no. But the walking-papers code is available at <a href="https://github.com/migurski/paperwalking">https://github.com/migurski/paperwalking</a> (written by the venerable <a href="http://mike.teczno.com/">Mike Migurski</a> of <a href="http://stamen.com/">Stamen</a>). We'll clean up our decoder and throw it on github at some point too.</p></blockquote>

<p>If someone wanted to learn how to use PIL and other python tools to digitize printed data, how would you suggest they go about doing it?</p>

<blockquote><p>I learned everything I know by playing with the tools available out there. It seems daunting at first, but once you start on a project, you suddenly find all these amazing libraries that make the impossible become possible and the difficult become easy. The <a href="http://www.pythonware.com/library/pil/handbook/index.htm">PIL tutorial and handbook</a> is a great place to start, as is the documentation for libraries like <a href="http://opencv.willowgarage.com/wiki/">OpenCV</a>, <a href="http://cairographics.org/pycairo/">pycairo</a>, and <a href="http://www.imagemagick.org/script/index.php">ImageMagick</a>.</p></blockquote>

<p>After you've collected a set of geospatial survey data, like you did here, what options do you have for aggregating it for analysis?</p>

<p>Correct me where I'm wrong, but it seems to me that tendermaps mainly tosses everything on the map and then allows users to filter it down using a set of browser knobs. I'm curious what other options there might be for mashing all the entries together and coming out with a finished product.</p>

<blockquote><p>That's a great question. We chose to throw everything onto the map is because it really showed the order within the chaos of two dozen handwritten maps on the same screen.</p>

<p>It would've been really cool to have different views into the people behind the data too. For example, we heard a great suggestion asking for a map of the paths that young women take through the tenderloin, because those paths are presumably safer. It would be really interesting to see maps diving into those sorts of verticals.</p></blockquote>

<p>Did you use <a href="http://geodjango.org/">GeoDjango</a> for this project? If so, how? If not, why not?</p>

<blockquote><p>Nope &mdash; the webserver backend is written with <a href="http://flask.pocoo.org/">Flask</a>. We georectified the tiles when saving them so we didn't need a geospatial database.</p></blockquote>

<p>Who all worked on the project, what role did they play, and how much time did they put in?</p>

<blockquote>I did all the back-end Python coding. <a href="http://twitter.com/#!/shashashasha">Sha Hwang</a> did all of the front-end (html/css/javascript). <a href="http://twitter.com/#!/the_hip_hapa">Jen Phillips</a> and <a href="http://twitter.com/#!/almostsci">Alan Rorie</a> went around the tenderloin and interviewed all the people who gave us maps. We were all at <a href="http://www.gaffta.org/">GAFFTA</a> working on tendermaps from Saturday morning to late Sunday afternoon.</blockquote>

<p>That's all I asked. If you have any more questions, drop them in the comments and maybe we can get Zain to answer them below.</p>
