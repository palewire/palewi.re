---
title: Ben's hip hop Twitter bot
slug: bens-hip-hop-twitter-bot
published_at: '2008-06-01T03:56:05-07:00'
wordpress_id: 126
---
<p>Has anyone else seen <a href="http://twitter.com/hemingway">@hemingway</a>, this weird Twitter feed that just spouts Ernie quotes every once in a while? Well, tonight I decided to code up my own twist on the idea. Follow <a href="http://twitter.com/mistadobalina">@mistadobalina</a> to receive hourly bursts of verse from one of my favorite albums, <a href="http://www.google.com/url?sa=t&amp;ct=res&amp;cd=2&amp;url=http%3A%2F%2Fwww.amazon.com%2FWish-Brother-George-Was-Here%2Fdp%2FB000002H9I&amp;ei=dn5CSOOeFonysAOLhNSjBg&amp;usg=AFQjCNE1R96LmcdFVDxaD33kaB_JJb3sIA&amp;sig2=4qG3KmVJGtOOuHwESjD9Mw">I Wish My Brother George Were Here</a> by <a href="http://www.google.com/url?sa=t&amp;ct=res&amp;cd=2&amp;url=http%3A%2F%2Fen.wikipedia.org%2Fwiki%2FDel_tha_Funkee_Homosapien&amp;ei=k35CSIz9EIm6sAPWvaiyBg&amp;usg=AFQjCNH0SiAPqRbXaXxHFXzZwu3v8NQxeQ&amp;sig2=rORRx4DJwQAeoU7DVEsNUA">Del Tha Funkee Homosapien</a>.</p>



<img src="https://palewire.s3.amazonaws.com/img/mistadobalina.png" alt="Screenshot of the @mistadobalina Twitter bot" />



<p>The whole thing is automated by about 30-45 minutes worth of work. So don't expect any miracles. But all the code is over <a href="http://github.com/palewire/mistadobalina/tree/master/mistadobalina.py">on github</a> if anybody wants it. I had a couple problems (no matter what album I asked for, I was only getting track listings for Staind), but <a href="http://lyricwiki.org/LyricWiki:SOAP">the LyricWiki SOAP service</a> is a pretty sweet Web service.</p>