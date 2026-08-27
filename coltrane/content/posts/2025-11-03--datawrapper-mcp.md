---
title: Chatting charts with the Datawrapper MCP
slug: datawrapper-mcp
published_at: '2025-11-03T07:16:05-08:00'
---
<figure>
  <video controls playsinline preload="metadata" aria-label="Demonstration of creating a Datawrapper chart with Claude Desktop.">
    <source src="/static/img/datawrapper-mcp.mp4" type="video/mp4">
  </video>
</figure>

<p>Today, I'm happy to release a new tool empowering chatbots like Anthropic's Claude to create charts with Datawrapper, a leading newsroom tool for publishing data.</p>

<p>It's an open-source Python library based on the Model Context Protocol (MCP) standard, an emerging technique intended to tame AI by teaching it to properly access external tools and data sources.</p>

<p>With it installed in Claude Desktop, your chatbot can create a Datawrapper chart with a prompt as simple as "Make a bar chart with this data: 2020,10 2021,15, 2022, 20."</p>

<p>Follow-on prompts like "make the bars blue," "add a source citation," or "publish the chart and give me the URL" will quickly update your initial work.</p>

<p>Testing it out, I've had fun asking the AI to suggest improvements to the chart, which I can then pick through to see what I'd like it to implement. That's where I think you can really see the power of harnessing the large-language models' creativity.</p>

<p>You can find the code on <a href="https://github.com/palewire/datawrapper-mcp">GitHub</a> and in the Python Package Index under the name <code>datawrapper-mcp</code>, where I've included installation instructions.</p>

<p>Be warned. This is still experimental technology. At this stage, I'm actively improving the integration. If you're not already a developer, it will take a sense of adventure — and perhaps a bit of vibecoding — to get started on your computer. I'm developing it in the open because I know it will benefit from others' experience and input.</p>

<p>This integration wouldn't be possible without the work our team at Reuters put into improving the underlying Python library for working with Datawrapper.</p>

<p>Thanks to recent investments of talent and time, our team has automated the creation of tens of thousands of breaking news charts by building pipelines that connect newsy data feeds to Datawrapper.</p>

<p>More than 120 have already appeared on our homepage.</p>
