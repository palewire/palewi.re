---
title: Introducing isobands
slug: introducing-isobands
published_at: '2026-08-19T03:25:28-07:00'
repr_image: https://palewi.re/static/img/introducing-isobands.gif
---
<img src="/static/img/introducing-isobands.gif" alt="Animated browser window showing the isobands documentation and a global temperature map.">

<p>Today, I'm happy to release <a href="https://palewi.re/docs/isobands/"><em>isobands</em></a>, an open-source library that makes it easier to present a dense dataset as a smoothed-out map.</p>

<p>It uses the handy Python programming language to access GDAL, a powerful geospatial toolkit that can be difficult to use on its own.</p>

<p>Feed <em>isobands</em> any gridded dataset — temperatures, pollution, whatever you'd like — and it will return filled contours that you can immediately publish with common platforms like MapLibre, Mapbox and Esri.</p>

<p>My take is that it fills a gap in the existing open-source ecosystem. The most common tools are great at generating the contour lines used to plot elevation, overlooking the polygons used in other cases, like the weather maps we're all used to seeing on television.</p>

<p>This release is an outgrowth of the <a href="https://www.linkedin.com/feed/update/urn:li:activity:7470478927887646720/">Reuters Climate Monitor</a>, our real-time dashboard that aims to track the slow-moving effects of climate change at the speed of news.</p>

<p>I hope to spin off more utilities from our work in the months ahead. Recent advances in machine learning make it easier than ever to package, document and release computer code.</p>

<p>You can see how I harness AI agents by checking out my <a href="https://github.com/palewire/python-open-source-template">template for Python projects</a>, which I recently overhauled to better take advantage of tools like GitHub Copilot, Anthropic's Claude and OpenAI's Codex.</p>
