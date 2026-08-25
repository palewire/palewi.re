---
title: Google Charts takes the Tufte Challenge
slug: google-charts-takes-tufte-challenge
published_at: '2010-03-10T13:13:57-08:00'
---
			<style type="text/css">
    .imgduobumper { clear:both; display:block; height:1em; }
    .imgduowrapper { display:block; }
    .imgduoleft { width:365px; margin-left:-2.5em; display:inline; float:left;}
    .imgduoright { float:right; width:365px; margin-right:-4.5em; display:inline;}
</style>
<p>They aren't interactive. They won't impress trendy developers. And they can look pretty hideous. They are <a href="http://code.google.com/apis/charttools/docs/choosing.html">Google Charts</a>. And, despite all that, they're kind of awesome.</p>

<div style="width:300px; float:left; margin-right:15px;">
<img src="http://chart.apis.google.com/chart?cht=p3&amp;chd=t:106,169,73,14&amp;chds=0,169&amp;chs=300x150&amp;chtt=Ocean+Area&amp;chdl=Atlantic|Pacific|Indian|Arctic&amp;chma=0,0,0,0|70&amp;chco=3366CC|DC3912|FF9900|109618&amp;chp=4.7" alt="Three-dimensional pie chart comparing the areas of the Atlantic, Pacific, Indian, and Arctic oceans" />
</div>
<p>I wouldn't blame you if you looked at this Google Chart, taken from the official documentation, and considered writing them off. The colors are garish. The data values are difficult to judge. The 3D shape muddles your view. The headline looks lame.</p>
<p>But behind that ugly chart is a powerful application. And if it's used wisely, it can live up to the highest standards.</p>
<h2>The Tufte Challenge</h2>
<p>For as long as I've been paying attention, people smarter than me have been talking about a guy named <a href="http://en.wikipedia.org/wiki/Edward_Tufte">Edward Tufte</a>. He's the <a href="http://en.wikipedia.org/wiki/Billy_graham">Billy Graham</a> of information graphics. Tufte travels the country, preaching his gospel to large crowds, encouraging designers to produce economical graphics that present data as clearly as possible.</p>
<p>In his widely recommended book <a href="http://www.edwardtufte.com/tufte/books_vdqi">The Visual Display of Quantitative Information</a>, Tufte lays out, step-by-step, how the standard bar chart can be tuned to perfection (pp. 126-128).</p>

<p>To prove once and for all that Google Charts need not be hideous, I will now use them to recreate Tufte's carefully crafted charts. And, with the guidance of my ingenious coworker <a href="http://www.google.com/search?q=Thomas+Suh+Lauder+site%3Awww.latimes.com&amp;ie=utf-8&amp;oe=utf-8&amp;aq=t&amp;rls=com.ubuntu:en-US:official&amp;client=firefox-a">Thomas Suh Lauder</a>, I will, just for the hell of it, attempt to surpass the master.</p>
<p>First, we start with a bar chart that Tufte describes as conventional. A picture from Tufte's book is on the left, and the Google Chart is on the right.</p>
<div class="imgduobumper"></div>
<div class="imgduowrapper">
<div class="imgduoright">
<img src="http://chart.apis.google.com/chart?chs=365x250&amp;cht=bvg&amp;chbh=15,5,15&amp;chd=t1:8,12,6,7,3,18,13,9,6,12,5,10&amp;chds=0,20&amp;chco=C8C8C8&amp;chxt=x,y,r,t&amp;chxs=0,C8C8C8,0,0,l,C8C8C8%7C1,C8C8C8,0,0,lt,C8C8C8%7C2,C8C8C8,0,0,lt,C8C8C8%7C3,C8C8C8,0,0,l,C8C8C8&amp;chxp=1,25,50,75%7C2,25,50,75&amp;chxtc=1,-5%7C2,-5" alt="Google recreation of Tufte's conventional bar chart" />
</div>
<div class="imgduoleft">
<img src="/static/img/tufte1.JPG" alt="Tufte's conventional bar chart" />
</div>
</div>
<div class="imgduobumper"></div>
<p>Since a Google Chart is nothing more than an automatically generated image, you can review the code for each one simply by right-clicking the image and copying out the URL.</p>

<p>Tufte's first move is to cut the ink along the border.</p>
<div class="imgduobumper"></div>
<div class="imgduowrapper">
<div class="imgduoright">
<img src="http://chart.apis.google.com/chart?chs=365x250&amp;cht=bvg&amp;chbh=15,5,15&amp;chd=t1:8,12,6,7,3,18,13,9,6,12,5,10&amp;chds=0,20&amp;chco=C8C8C8&amp;chxt=x,y&amp;chxs=0,C8C8C8,0,0,l,C8C8C8%7C1,C8C8C8,0,0,lt,C8C8C8&amp;chxp=1,25,50,75&amp;chxtc=1,-5" alt="Google recreation of Tufte's bar chart with the border removed" />
</div>
<div class="imgduoleft">
<img src="/media/img/tufte2.JPG" alt="Tufte's bar chart with the border removed" />
</div>
</div>
<div class="imgduobumper"></div>
<p>Then he clips the y-axis, leaving the tick marks.</p>
<div class="imgduobumper"></div>
<div class="imgduowrapper">
<div class="imgduoright">

<img src="http://chart.apis.google.com/chart?chs=365x250&amp;cht=bvg&amp;chbh=15,5,15&amp;chd=t1:8,12,6,7,3,18,13,9,6,12,5,10&amp;chds=0,20&amp;chco=C8C8C8&amp;chxt=x,y&amp;chxs=0,C8C8C8,0,0,l,C8C8C8%7C1,ffffff,0,0,t,000000&amp;chxp=1,25,50,75&amp;chxtc=1,-5" alt="Google recreation of Tufte's bar chart with the y-axis removed" />
</div>
<div class="imgduoleft">
<img src="http://www.palewire.com/media/img/tufte3.JPG" alt="Tufte's bar chart with the y-axis removed and tick marks retained" />
</div>
</div>
<div class="imgduobumper"></div>
<p>Tufte raises the ante by inserting white coordinate lines that segment each bar at the y-axis intervals, something I've matched thanks to a hack Tom developed. Tufte also removes the tick marks, replacing them with y-axis labels.</p>
<div class="imgduobumper"></div>
<div class="imgduowrapper">
<div class="imgduoright">
<img src="http://chart.apis.google.com/chart?chs=450x250&amp;cht=bvg&amp;chbh=15,5,15&amp;chd=t1:0,8,12,6,7,3,18,13,9,6,12,5,10,0|5,5,5,5,5,5,5,5,5,5,5,5,5,5|10,10,10,10,10,10,10,10,10,10,10,10,10,10|15,15,15,15,15,15,15,15,15,15,15,15,15,15&amp;chds=0,20&amp;chco=ffffff|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|ffffff&amp;chxt=x,y&amp;chxs=1,000000,13,0,t|0,ffffff,13,1,lt,ffffff&amp;chxtc=1,0&amp;chm=D,FFFFFF,1,0,1,1|D,FFFFFF,2,0,1,1|D,FFFFFF,3,0,1,15&amp;chxp=1,25,50,75&amp;chxl=1:|5%|10%|15%|0:|" alt="Google recreation of Tufte's bar chart with coordinate lines and y-axis labels" />
</div>
<div class="imgduoleft">
<img src="http://www.palewire.com/media/img/tufte4.JPG" alt="Tufte's bar chart with coordinate lines and y-axis labels" />
</div>

</div>
<div class="imgduobumper"></div>
<p>And, with his final move, Tufte removes the y-axis labels.

<div class="imgduobumper"></div>
<div class="imgduowrapper">
<div class="imgduoright">
<img src="http://chart.apis.google.com/chart?chs=450x250&amp;cht=bvg&amp;chbh=15,5,15&amp;chd=t1:0,8,12,6,7,3,18,13,9,6,12,5,10,0%7C5,5,5,5,5,5,5,5,5,5,5,5,5,5%7C10,10,10,10,10,10,10,10,10,10,10,10,10,10%7C15,15,15,15,15,15,15,15,15,15,15,15,15,15&amp;chds=0,20&amp;chco=ffffff%7CC8C8C8%7CC8C8C8%7CC8C8C8%7CC8C8C8%7CC8C8C8%7CC8C8C8%7CC8C8C8%7CC8C8C8%7CC8C8C8%7CC8C8C8%7CC8C8C8%7CC8C8C8%7Cffffff&amp;chxt=x,y&amp;chxs=0,ffffff,0,0,t,ffffff%7C1,ffffff,13,1,t,ffffff&amp;chxtc=1,0&amp;chm=D,FFFFFF,1,0,1,1%7CD,FFFFFF,2,0,1,1%7CD,FFFFFF,3,0,1,15&amp;chxs=0,C8C8C8,0,0,l,C8C8C8|1,ffffff,0,0,t,000000&amp;chxp=1,0&amp;chxl=|0:||J|F|M|A|M|J|J|A|S|O|N|D" alt="Google recreation of Tufte's bar chart with y-axis labels removed" />
</div>
<div class="imgduoleft">
<img src="http://www.palewire.com/media/img/tufte5.JPG" alt="Tufte's bar chart with y-axis labels removed" />
</div>
</div>
<div class="imgduobumper"></div>
</p><p>Now, for the fun part. We will defy the master. We will improve the chart.</p>
<p>First, by adding x-axis labels that indicate the difference between each column. I like to imagine there's one bar for each month.</p>

<div class="imgduobumper"></div>
<div class="imgduowrapper">
<div style="margin-left:7em; width:365px; display:inline;">
<img src="http://chart.apis.google.com/chart?chs=450x250&amp;cht=bvg&amp;chbh=15,5,15&amp;chd=t1:0,8,12,6,7,3,18,13,9,6,12,5,10,0|5,5,5,5,5,5,5,5,5,5,5,5,5,5|10,10,10,10,10,10,10,10,10,10,10,10,10,10|15,15,15,15,15,15,15,15,15,15,15,15,15,15&amp;chds=0,20&amp;chco=ffffff|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|ffffff&amp;chxt=x,y&amp;chxs=1,ffffff,13,0,t|0,000000,13,0,l,000000&amp;chxtc=1,0ffffff&amp;chm=D,FFFFFF,1,0,1,1|D,FFFFFF,2,0,1,1|D,FFFFFF,3,0,1,15&amp;chxp=1,0&amp;chxl=|0:||J|F|M|A|M|J|J|A|S|O|N|D" alt="Google bar chart with monthly labels" />
</div>
</div>
<div class="imgduobumper"></div>
<p>Then we will add the precise y-axis value for each bar, which gives the reader a much higher level of precision than any previous indicator.</p>
<div class="imgduobumper"></div>
<div class="imgduowrapper">
<div style="margin-left:7em; width:365px; display:inline;">
<img src="http://chart.apis.google.com/chart?chs=450x250&amp;cht=bvg&amp;chbh=15,5,15&amp;chd=t1:0,8,12,6,7,3,18,13,9,6,12,5,10,0|5,5,5,5,5,5,5,5,5,5,5,5,5,5|10,10,10,10,10,10,10,10,10,10,10,10,10,10|15,15,15,15,15,15,15,15,15,15,15,15,15,15&amp;chds=0,20&amp;chco=ffffff|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|C8C8C8|ffffff&amp;chxt=x,y&amp;chxs=1,ffffff,13,0,t|0,000000,13,0,l,000000&amp;chxtc=1,0ffffff&amp;chm=D,FFFFFF,1,0,1,1|D,FFFFFF,2,0,1,1|D,FFFFFF,3,0,1,15|N,000000,0,1,12|N,000000,0,2,12|N,000000,0,3,11|N,000000,0,4,11|N,000000,0,5,11|N,000000,0,6,11|N,000000,0,7,11|N,000000,0,8,11|N,000000,0,9,11|N,000000,0,10,11|N,000000,0,11,11|N,000000,0,12,11&amp;chxp=1,0&amp;chxl=|0:||J|F|M|A|M|J|J|A|S|O|N|D" alt="Google bar chart with monthly labels and exact values" />
</div>
</div>
<div class="imgduobumper"></div>
<h2>That's cute, but now what?</h2>

<p>
    Good question. None of these example make Google Charts any easier to figure out. And, let's be real, those <a href="http://code.google.com/apis/chart/docs/chart_params.html">crazy URL parameters</a> are tough to get your head around.
</p>
<p>
    My hope is this exercise can convince you that Google Charts shouldn't be dismissed. They can look halfway good.
</p>
<p>But, beyond appearances, they have a lot going for them on the backend, too.</p>
<p>If you integrate Google Charts with a database framework like Django,
    you can scale to the moon. At the Los Angeles Times, we use a branch of Jacob Kaplan-Moss's <a href="http://github.com/jacobian/django-googlecharts">django-googlecharts</a>
    to automatically generate thousands of charts about Census data in
    <a href="http://mappingla.com/north-hollywood">L.A. neighborhoods</a> (check out the accordions). We can easily pull off Tom's coordinate line hack using some code I patched to the app. And, thanks to the magic of Python, we do it all without crafting a single crazy URL. 

</p>
<p><a href="http://projects.latimes.com/hollywood/star-walk/about/#star-types">Elsewhere</a>,
    we integrate a one-off Google Charts with a little CSS to mimic the style of the newspaper online. That's something you could replicate with the handy <a href="http://dexautomation.com/googlechartgenerator.php">Google Chart Creator</a> and a well-crafted HTML wrapper.
</p>
<p>Once you're flying, Google Charts can save you a lot of time. You can make Tufte-approved charts without the help of a Flash developer or outside designer. And since they're nothing more than flat image files, they will immediately work in even <a href="http://en.wikipedia.org/wiki/Internet_Explorer_6">the most difficult environments</a>. What's not to love?</p>
			
