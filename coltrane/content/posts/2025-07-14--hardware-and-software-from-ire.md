---
title: Hardware and software from IRE
slug: hardware-and-software-from-ire
published_at: '2025-07-14T04:51:34-07:00'
repr_image: https://palewi.re/static/img/hardware-and-software-from-ire-1.jpg
---

<img src="/static/img/hardware-and-software-from-ire-1.jpg" alt="Screenshot of a WNYC Radio Program archive page with an audio player.">

<p>Some unexpected hardware arrived in the mail from Investigative Reporters and Editors over the weekend.</p>

<p>It's a thank you for my volunteer work cleaning up the organization's archives as it prepares to launch a new website.</p>

<p>While the fruits of our labor won't be visible for a bit, one trick we figured out might be more broadly useful to newsroom nerds.</p>

<p>I took on a challenge to transcribe the thousands of recordings of IRE trainings, panels and other events the organization has accumulated over the years. By converting them into text, our hope is that we can create a searchable database where members can mine our communal knowledge.</p>

<p>You can see how I got it done by browsing this new open-source <a href="https://github.com/palewire/wnyc-radio-archive-transcriber">code repository</a>, which applies the techniques I learned to a public domain source: the WNYC Radio archives held by city librarians.</p>

<p>It includes all the code and instructions you need to scrape audio files off the web and feed them to OpenAI's groundbreaking Whisper transcription service. By leaning on GitHub Actions' parallel processing system, my code can chew through 256 files at a time, quickly working through thousands of broadcasts.</p>

<p>And, get this, because of GitHub's generous policy towards open-source projects, the whole thing is free. I can imagine using the same toolkit in the newsroom to transcribe government meetings, political podcasts and any number of other newsworthy sources.</p>

<p>You can learn more about how newsrooms can use GitHub Actions to grind data by checking out <a href="https://palewi.re/docs/go-big-with-github-actions/">Go Big with GitHub Actions</a>, the free textbook that Iris Lee, Dana Chiueh and I released at IRE's most recent data journalism conference. It includes even more examples of how journalists are using cloud computing to gather, refine and analyze data.</p>
