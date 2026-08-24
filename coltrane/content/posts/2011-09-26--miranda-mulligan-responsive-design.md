---
title: 'Q&A: Miranda Mulligan dishes on responsive design'
slug: miranda-mulligan-responsive-design
published_at: '2011-09-26T18:37:55-07:00'
---
<p>The <a href="http://www.alistapart.com/articles/responsive-web-design/">"responsive design"</a> of the new <a href="http://bostonglobe.com">bostonglobe.com</a> is one of the most talked about newspaper.com events of the year. Built using a system that tailors the page's design to the user's device, it sizes down for mobile phones and sizes up for desktop monitors.</p>

<p>To learn more about how it happened, I conducted an email interview with <a href="http://www.linkedin.com/in/mirandamulligan">Miranda Mulligan</a>, the Globe's digital design director.</p>

<p>You can read the entire transcript below, but here are my quick takeaways:</p>

<ul>
    <li>The new bostonglobe.com took a year "from inception to launch."</li>
    <li>Mulligan thinks the technology's cross-platform potential makes it "not a terribly hard sell" to the business side.</li>
    <li>The new frontend is rolling out with a new CMS backend and "everyone's jobs changed."</li>
    <li>Mulligan underscores that boston.com and bostonglobe.com are "two different products."</li>
    <li>Mulligan is with the legion of developers who think making sites "comp to code needs a rethink."</li>
    <li>Existing open-source kits for responsive design don't cut it.</li>
    <li>Getting display ads to work across devices is difficult and still needs work.</li>
</ul>

<div class="detailborderbreak"></div>

<p>How long did this take, from beginning to launch?</p>

<blockquote><p><a href="https://twitter.com/#!/jeffmoriarty">Jeff Moriarty</a>, our VP of Product and Development had started working on defining the new site (<a href="http://bostonglobe.com">BostonGlobe.com</a>) in late summer of last year. He and <a href="http://www.linkedin.com/pub/dan-zedek/3/b96/872">Dan Zedek</a> had conceived some of the early prototypes and when I joined the Globe (in September), I joined the party. We found a great partner for the visual design of the site in <a href="http://upstatement.com/">Upstatement</a> and <a href="http://www.filamentgroup.com/">Filament Group</a> and <a href="http://unstoppablerobotninja.com/about/">Ethan Marcotte</a> joined us in the end of the year. So, I'd say it took a little over a year from inception to launch. However, we began a deep dive on the design and build of this site -- from scratch -- at the beginning of this year.</p></blockquote>

<p>How does a geek concept like responsive design germinate inside a newspaper company like the Boston Globe? Print media executives are reputed to be totally out of it. So how was the idea sold internally?</p>

<blockquote><p>When defining the news site, Jeff had become obsessed with idea of having it available at any entry point: desktop, tablet and mobile. It is easy to become overwhelmed by the ever-increasing range of devices in the market and it is not realistic to try and design for everything. In the fall, we met <a href="http://www.linkedin.com/in/toddparker">Todd Parker</a> and <a href="http://www.linkedin.com/profile/view?id=1401177">Patty Toland</a> at The Filament Group in Boston, whose team had popularized the concept of <a href="http://en.wikipedia.org/wiki/Progressive_enhancement">progressive enhancement</a>. (In fact, my second week of working at the Globe, Jeff walked by my desk, dropped off a copy of <a href="http://www.filamentgroup.com/dwpe/">their book</a> and said "Weekend homework.") As we talked to them about our project, they thought to reach out to Ethan to see if he was interested in joining the party. By the time we were all gathering for an official kickoff, it was really exciting that we were on the same page and the next step was to figure out if we could do it.</p>

<p>Also, I think the other half of your question is getting at the idea that it takes a lot of internal stakeholder buy-in to turn a large ship, correct?:</p>

<p>Well, when you think of what we were trying to do from 30,000 feet, it was not a terribly hard sell. At its root, this design approach takes full advantage of the most popular app on any device – the Web browser. So, we are not even asking users to go download something to read our content. Also, it should be understood, BostonGlobe.com is a new product. There is no legacy. The Globe content has always been digitally published to <a href="http://boston.com">Boston.com</a>, with a primary entry point of "Today's Globe" section of Boston.com. We also have an Adobe Air-based paid app called <a href="http://boston.com/bostonglobe/reader/">GlobeReader</a> that’s been available for the past several years. After much research, there seemed to be an argument to be made there was an audience for a long-form, immersive reading experience like the one we have tried to create for BostonGlobe.com. It really has been an incredible year to work for The Boston Globe.</p>

<p>Also, I am not sure that it is fair to dump all large, 'old media' news organizations into the same 'Print media executives are reputed to be totally out of it' bucket. I balk at the idea that you have to go the journalism-start-up route in order to try something fresh. In my experience, the are some really awesome, smart people in the trenches as well as at the executive table.</p></blockquote>

<p>The cosmetic changes between boston.com and bostonglobe.com look drastic. Is the same true for the backend? How does the new site integrate with your preexisting CMS? How has it changed the staffing and workflow (i.e. photo cropping, CMS jockeying) necessary to publish each day?</p>

<blockquote><p>Actually we are currently implementing a new CMS and BostonGlobe.com is the first of the publishing points to go on it. Next will be the print edition of The Boston Globe and we will be moving Boston.com into it next year. The new CMS meant everyone's jobs changed: i.e. how reporters filed their stories, how budgets were managed, how picture editors attached photos to stories, copy editors, artists, designers etc. The managing editor likes to joke that we have changed everything that we could possibly change digitally in 2011 including our email client.</p>

<p>Also, it should be understood, Boston.com and BostonGlobe.com are two different products, intended for two different audiences.</p></blockquote>

<p>How does a design system like this adjust to the demands of a newspaper site? I noticed that the second column tends to jump to the top on smaller devices. Why did you do that? And what other things are baked in that are different from an off the shelf responsive-design kit?</p>

<blockquote><p>In short, there isn't really an "off-the-shelf responsive design kit" In fact, we talk about the design process being heavily reliant on a highly collaborative, design-development cycle. It involves rapid prototyping and designing, mostly, in the browser. Web design has two buckets, right? Visual design and interaction design. Therefore, the traditional process of going from comp to code needs a rethink, especially when designing a responsive site.</p>

<p>So, really, the way the content reflows at different breakpoints is on purpose. We tried to maintain the content hierarchy as much as possible not take away any content just because the user is on a phone, for example. (And, yes, we have some display bugs that we are working out still, but hey, it's about constant refinement, right?) Basically, we were fighting the adage that 'mobile | desktop' have become synonyms for 'less | more'.</p></blockquote>

<p>There are some ready-to-serve sets like <a href="http://getskeleton.com/">getskeleton.com</a> and <a href="http://cssgrid.net/">cssgrid.net</a> that claim to be a quick-and-dirty framework for making it happen. How would you distinguish your system from those sorts of things?</p>

<blockquote><p>I balk at the idea that there is a 'responsive design' button that can be pushed... Those sets are fine but do not automatically include some of the patches that came out of this project  such as the responsive images solution which deals with the size of images being served depending on the breakpoints. Thinking about page weight is especially important in responsive design.</p>

<p>So, sure, those examples are fine starting points so long as the end result has a fluid foundation, has flexible images and media, and utilizes media queries from the CSS3 specification.</p></blockquote>

<p>In <a href="http://www.readwriteweb.com/mobile/2011/09/how-the-boston-globe-pulled-ofp2.php">an interview with ReadWriteWeb</a>, a Globe staffer said that the "ugly" JavaScript code commonly found in online advertisements created an "unresolved" issue for your team. Another said interstitials and takeovers simple can't be done. How does this problem get resolved?</p>

<blockquote><p>These are not Globe employees. These are our contractors. But to answer your question:
We are working with our advertisers and constantly refining the ad serving solution. It has definitely been one of the major challenges.</p></blockquote>

<p>Finally, how does a design like this turn up the volume for big news? If the Red Sox win the World Series in a few weeks, how do you blow it out?</p>

<blockquote><p>We designed out several views for the homepage given different news presentation scenarios... Just like we have always done. </p></blockquote>