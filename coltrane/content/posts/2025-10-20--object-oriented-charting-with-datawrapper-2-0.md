---
title: Object-oriented charting with Datawrapper 2.0
slug: object-oriented-charting-with-datawrapper-2-0
published_at: '2025-10-20T05:45:37-07:00'
repr_image: https://palewi.re/static/img/object-oriented-charting-with-datawrapper-2-0-1.jpg
---
<img src="/static/img/object-oriented-charting-with-datawrapper-2-0-1.jpg" alt="Browser-framed screenshot of Datawrapper's line chart documentation.">

<p>I'm pleased to release version 2.0 of the open-source tool for creating Datawrapper charts with the Python programming language.</p>

<p>The new edition makes it easier than ever for journalists to automate charts and maps. And it lays the groundwork for even bigger strides in the dawning era of AI assistants.</p>

<p>We've completely redesigned the approach for simplicity and speed. Users are no longer required to struggle with decoding arcane configuration options or wrestle with the complex data structures of the Datawrapper API.</p>

<p>Chart types are now defined in a legible, consistent style, known to the real nerds as "object-oriented programming," with well-documented options, clearly defined data types, and proper validation.</p>

<p>Creating a new chart is now as simple as:</p>

<pre lang="python">dw.BarChart(
    title="Most Popular Programming Languages in 2025",
    data=data,
).create()</pre>

<p>This approach to Python is well-positioned to surf the new wave of Generative AI tools rushing out from companies like Anthropic, OpenAI and GitHub. In the weeks and months ahead, we will be experimenting with the emerging Model Context Protocol standard to see if chatbots can use our code to make charts. I'm betting the answer is yes.</p>

<p>Today's release is the product of months of work here at Reuters, where our team has automated the creation of tens of thousands of breaking news charts by building pipelines that connect newsy data feeds to Datawrapper.</p>

<p>More than 120 have already appeared on our homepage.</p>

<p>This work required painstaking study of the Datawrapper API and hours of careful experimentation by Iris Lee, Grant Smith, Rhyannon Bartlett-Imadegawa and myself. I'm proud that we're able to share what we've learned and hope it can help you get things done. I'm certain that we will benefit from the contributions of others to the tool.</p>

<p>You can see the new code for yourself in our newly expanded <a href="https://datawrapper.readthedocs.io/">Datawrapper documentation</a> or by visiting <a href="https://github.com/chekos/Datawrapper/">the repository</a>.</p>

<img src="/static/img/object-oriented-charting-with-datawrapper-2-0-2.jpg" alt="Browser-framed screenshot of the First Automated Chart tutorial on palewi.re.">

<p>I've also updated my online tutorial, <a href="https://palewi.re/docs/first-automated-chart/">First Automated Chart</a>, to guide newbies on how to use the revised system.</p>

<p>This expansion is an outgrowth of pioneering by the library's founder and maintainer, Sergio Sanchez. It wouldn't exist without him. Thank you, Sergio!</p>
