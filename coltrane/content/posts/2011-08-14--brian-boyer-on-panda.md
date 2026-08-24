---
title: 'Q&A: Brian Boyer on the plan for PANDA'
slug: brian-boyer-on-panda
published_at: '2011-08-14T22:51:05-07:00'
---
<p>This summer, the Chicago Tribune won <a href="http://www.knightfoundation.org/grants/20110152/">a $150,000 grant</a> through the Knight News Challenge to create PANDA, a software tool aimed at helping reporters clean up data. To find out more about it, I conducted an email interview with the project's leader, <a href="http://hackerjournalist.net/">Brian Boyer</a>.</p>

<p>You can read the entire transcript below, but here are the quick takeaways I had:</p>

<ul>
    <li>PANDA is conceived as an online warehouse where newsrooms can store data sets.</li>
    <li>To me, it sounds like some combination of Google Refine and Google Fusion Tables tailored to suit newsroom needs.</li>
    <li>Any newsroom will be allowed to use it, and they shouldn't need a full-time geek to make it work.</li>
    <li>All of the code will be open on <a href="http://github.com">Github</a> "from day one" under an <a href="http://en.wikipedia.org/wiki/MIT_License">MIT license</a>.</li>
</ul>

<p>It must be said, I'm biased. Brian and I work for <a href="http://www.tribune.com/">the same parent company</a> and I'm rooting for him to succeed. So if you think I'm letting him off the hook, fire away in the comments and we'll see if we can keep him answering.</p>

<div id="detailborderbumper" class="thin"></div>

<p>In <a href="http://www.knightfoundation.org/grants/20110152/">a video about PANDA</a> on the Knight News Challenge's website, you describe it as a "newsroom data appliance." What is that?</p>

<blockquote><p>PANDA will be a place for folks in the newsroom to stash their data,
and a tool for helping reporters search and compare data sets. It will
not be a publishing tool, and is not intended to address the needs of
readers. It will be an appliance in the same way Google sells
appliances for your intranet -- it will be a cloud-hosted system,
provisioned for each newsroom that signs up. Each newsroom will pay
their own hosting costs, which we will try to keep very low.</p></blockquote>

<p>How will it be different from something like <a href="http://en.wikipedia.org/wiki/Google_Fusion_Tables">Google Fusion Tables?</a></p>

<blockquote><p>We envision Google Fusion Tables as one of many ways you can further
explore or present your data, after it's been run through PANDA. Alex
Howard wrote up a good piece the other day about an idea that Jonathan
Stray and I were talking about: <a href="http://radar.oreilly.com/2011/07/data-journalism-tools-newsroom-stack.html">the newsroom stack</a>.</p>

<p>The stack would be your kit of tools you use to deal with data, and
each tool helps with a different layer of abstraction.</p>

<p>So for example, you write a FOIA and they send you a group of
100-column Excel files. (Each numbered step is sort of a concept, each
tool is, in my mind, a layer of the stack. This may be better as an
infographic with arrows and icons.)</p>

<p>1. Prepare the data<br>
Excel: Save each file to CSV<br>
CSVKit: Join the files into one, and cut out the columns you don't care for<br>
Refine: Normalize the hand-entered values in the columns<br></p>

<p>2. Find stuff<br>
Refine + PANDA: Compare your dataset to other datasets you've got in PANDA<br>
PANDA: Upload the dataset (and original docs, for archival purposes)<br>
so you can search through it quickly, and so that your peers can see
it easily</p>

<p>3. Explore in other tools and/or publish<br>
Google Fusion Tables: Export the dataset (or a subset) to FT to see it on a map<br>
Overview (Mr. Stray's project): Export to do fancy semantic stuff<br>
TileMill: Export to make sweet slippy maps<br>
PostGIS/QGIS: Export to a database to do proper GIS analysis</p></blockquote>

<p>So you see PANDA as integrating with <a href="http://code.google.com/p/google-refine/">Google's Refine?</a> How would that work?</p>

<blockquote><p>Refine was originally created as a tool to tidy up data on it's way
into Freebase. One of it's fancier features is to compare one of your
columns with data in Freebase. So for instance, your dataset is a list
of all the dogs registered in your county.</p>

<p>The first thing you'd do is clean up the column of the dogs' breeds.
Refine gives you great tools to find clusters of similar values
(Golden Retriever, Golden Retreiver, Golden Retr, etc.) and replace
them with a single proper value.</p>

<p>But let's say that you want to know the popularity of the breeds.
Well, you can instruct Refine to join to tables in Freebase, and carry
over columns of data. So, you can match up your newly-tidy breed
column to the list of dog breeds in Freebase, and add the Kennel Club
Ranking column from Freebase to your dataset.</p>

<p>So, back to PANDA... re-read the above example, but replace "dogs"
with "campaign donors", "breeds" with "companies a person works for",
"Kennel Club Ranking" with "payments for services rendered to city
agencies".</p>

<p>Or something. I don't have a perfect example because if I did, we'd
have written the story, or I wouldn't be writing about it. I'm hoping
that reporters will find interesting ways to join up data sets that we
haven't yet thought of -- it will be a somewhat open-ended tool.</p></blockquote>

<p>Will you be incorporating code from Refine, or mimicking it?</p>

<blockquote><p>Refine has a plugin architecture. The plan is that folks would use
Refine, with a PANDA plugin.</p></blockquote>

<p>Existing sites like Google Fusion Tables have incredible features, but tend to bog down on large datasets. Will PANDA be able to work with datasets that contain tens of thousands &mdash; or, for that matter, hundreds of thousands &mdash; of records?</p>

<blockquote><p>We were just discussing multi-million row datasets (like voter
registration lists) and the consensus was yes, we absolutely must
handle data that big.</p></blockquote>

<p>What's the development plan? Who will be building what? And will any of the code or tickets or anything be online before the initial release?</p>

<blockquote><p>All the code and tickets will be on GitHub from day one. We don't have
a detailed development plan yet -- when we get our first check from
Knight, we'll start working on the project in earnest. We'll have a
full-time developer on staff for the length of the grant (one year)
and part-time/contract help for design and UX work.</p></blockquote>

<p>Who will be allowed to use PANDA? Will be limited to news organizations you approve, like DocumentCloud, or will anyone be able to create an account?</p>

<blockquote><p>We plan to make PANDA freely available to anybody who finds a use for
it. That said, PANDA will be built with news organizations in mind, so
if folks want a general-purpose data appliance (instead of a newsroom
data appliance), they're welcome to fork the code and modify it for
their own use.</p></blockquote>

<p>Will a newsroom need a developer, like the people on your team, to participate? Or will they be able to sign up and throw reporters at it?</p>

<blockquote><p>The goal is to create a system that a newsroom can fire up with no
technical people on-hand. You'll likely get more out of PANDA if
you've got data manipulation skills, but that won't be a requirement.</p></blockquote>

<p>Finally, what software license will you release under? And how was that worked out with Knight?</p>

<blockquote><p>MIT. I don't think we really worked it out. But that's the plan!</p></blockquote>