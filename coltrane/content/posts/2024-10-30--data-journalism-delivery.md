---
title: Data dashboards on Reuters.com
slug: data-journalism-delivery
published_at: '2024-10-30T12:00:00-07:00'
repr_image: https://palewi.re/static/img/data-dashboards-at-reuters-1.jpg
---
<img src="/static/img/data-dashboards-at-reuters-1.jpg" alt="Screenshot of the Reuters Magnificent Seven Monitor's Trading Momentum chart comparing the Magnificent Seven with the rest of the S&amp;P 500.">

<p>Minor milestone today at Reuters.</p>

<p>Data dashboards are now one of our standard storytelling templates, joining the familiar arsenal of text articles, photo galleries and blogs. Going forward, publishing a live-updating collection of charts, maps and tables will require nothing more than a few points and clicks.</p>

<p>First through the gate is “<a href="https://www.reuters.com/data/magnificent-seven-monitor-2024-10-30/">The Magnificent Seven Monitor</a>,” which tracks the ongoing performance of the heavyweight U.S. technology stocks that dominate the market.</p>

<p>Anyone who has toiled in the vineyards of news knows it’s hard to integrate custom designs like this into the rigid, cookie-cutter “content-management systems” that power most media sites. As a result, many data projects and long-form investigations are published off-the-reservation using shadow technology.</p>

<p>While there are advantages to working outside your core platform, there are downsides, too. Every new publishing tool must tackle how to integrate with your site design, your homepage, your recirculation system, your ads, your analytics, your paywall, and the workflow of your colleagues. That’s a lot.</p>

<p>At Reuters, we aim to bridge the divide once and for all. That requires treating the innovative story forms pioneered over the last twenty years — multimedia stories, interactive visuals, live-updating data — like the other widgets we manufacture in our “CMS.”</p>

<p>Today’s release is a modest first step in that direction. Now that we have the technology issues sorted out, we’ll do more and better in the months ahead. Give it a look. Let me know what sucks, and what more we could do. I am happy to answer any Q’s in the comments.</p>

<p>Here are a couple of extras for the nerds.</p>

<p>Our original work in the tracker, which you won’t find elsewhere, is a composite ticker that lumps all seven stocks into a single number and my attempt to simplify the “stochastic oscillators” favored by Wall Street “technicals.”</p>

<img src="/static/img/data-dashboards-at-reuters-2.jpg" alt="Screenshot of the Python stochastic_oscillator function used for the Magnificent Seven Monitor's momentum calculation.">

<p>Here’s the <a href="https://gist.github.com/palewire/045717b87e210867f70f71f0015609d4">code that runs the momentum calculation</a>. Feel free to hate it!</p>

<p>Not into numbers? Word nerds can read <a href="https://www.reuters.com/data/man-behind-magnificent-seven-2024-10-30/">my interview with Michael Harnett</a>, the Bank of America analyst who dubbed the group, also out today.</p>
