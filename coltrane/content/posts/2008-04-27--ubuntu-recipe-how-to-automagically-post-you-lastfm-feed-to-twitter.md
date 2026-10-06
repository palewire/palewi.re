---
title: 'Ubuntu recipe: Post your Last.fm feed to Twitter'
slug: ubuntu-recipe-how-to-automagically-post-you-lastfm-feed-to-twitter
published_at: '2008-04-27T12:12:13-07:00'
wordpress_id: 114
---
<p>I signed up for Twitter this morning, opening an account at <a href="http://twitter.com/palewire">http://twitter.com/palewire</a>. Since I haven't seen or heard from my cell phone in a week or two, don't count on much on the scene reporting. But I did take a few minutes this morning to line up <a href="http://www.last.fm/user/palewire">my Last.fm feed</a>, so that my lastest listenings are now automatically Twittered to the huddled masses yearning to have my musical taste shoved down their throat.</p>



<p>For any other Ubuntu users who'd like to follow along, here's a quick recap on how I made it happen.</p>



<p>1. Move to the folder where you store random scripts. Me, I use...</p>



<pre lang="bash">cd /usr/local/bin</pre>



<p>2. Create a new Perl script and open it in gedit.</p>



<pre lang="bash">sudo gedit twitter_fm.pl</pre>



<p>3. Copy and paste in the <a href="http://walterhiggins.net/lastfm_to_twitter.html">ready-to-serve code</a> provided by Walter Higgins.</p>



<p>4. Edit in your Twitter and Last.fm login information. Save and exit the file.</p>



<p>5. Create a new shell script.</p>



<pre lang="bash">sudo gedit twitter_fm.sh</pre>



<p>6. Paste in the following, editing the folder structure to reflect wherever you stuck your steez.</p>



<pre lang="shell">#!/bin/sh



perl /usr/local/bin/twitter_fm.pl</pre>



<p>7. Set the shell script so it becomes executable.</p>



<pre lang="bash">sudo chmod +x twitter_fm.sh</pre>



<p>8. Navigate through the System>Preferences>Session menu as described <a href="http://www.howtogeek.com/howto/ubuntu/how-to-add-a-program-to-the-ubuntu-startup-list-after-login/">here</a> and add the shell script to your startup processes.</p>



<p>9. Restart!</p>



<p>I just patched this mess together a couple minutes ago, so there might be some bugs. Either in my setup or in Walter's script. Don't know yet. Let me know if you see anything idiotic on my part. </p>



<p>I also installed Wordpress's <a href="http://wordpress.org/extend/plugins/twitter-tools/">Twitter Tools</a> plugin, so now my latest blog posts will also be sent out via Twitter.</p>



<p>Also on the Twitter tip, earlier this week we launched a feed at work for our popular political blog, <a href="http://latimesblogs.latimes.com/washington/">Top of the Ticket</a>. It includes the latest posts from our team of writers, and, on election nights, live election results as they come in. You can sign up <a href="http://twitter.com/latimestot">here</a>. For anyone looking to reroute their own data streams to Twitter, I can't recommend Chris Thompon's <a href="http://search.cpan.org/~cthom/Net-Twitter-1.06/lib/Net/Twitter.pm">Net::Twitter</a>  Perl module enough. Easy. Peasy.</p>