---
title: 'Terminal recipe: download an entire web site with wget'
slug: terminal-recipe-how-to-download-an-entire-web-site-with-wget
published_at: '2008-06-15T09:05:15-07:00'
wordpress_id: 128
---
<p>From time to time, an occasion might arise when you'd like to download an entire Web site. At my old job, I liked to pull down government sites and go on fishing expeditions with Google Desktop Search for hot terms (ex. names of corporations and political appointees) or certain file types (ex. Excel, Access, CSV, et cetera). And the other day at my current job <a href="http://www.latimes.com/la-me-kozinski12-2008jun12,0,778115.story">a situation</a> cropped up where the newsroom wanted to download a bunch of files quickly, so it was handy to set a spider loose rather than sit there and try to download everything click by click.</p>

<p>One way to handle the job is to use a command-line utility called <a href="http://www.gnu.org/software/wget/">wget</a> to crawl your target and mirror its files on your local computer.</p>

<p>If you're working on a Macbook, the first thing you'll need to do is install wget. I'd suggest you do that by downloading the latest version and compiling the binary from the source code. That might sound scary, but it's just a fancy way of saying you're going to install something from the command line instead of clicking a bunch of pretty boxes. Some other sites are going to push you toward pretty boxes and maybe even this big bloated thing called Fink, but, trust me on this one, it's going to be a lot easier for you down the road if you learn how to install stuff yourself. And this is a simple enough example that it's worth the shot.</p>

<p>So, if you're with me, before you do anything else, download and install <a href="http://developer.apple.com/tools/xcode/">Mac's XCode</a>, which includes the compilers you'll need to build stuff on your own.</p>

<p>Then just open your terminal and let rip with the following...</p>

<pre lang="Bash">mkdir src
cd src
curl -O http://ftp.gnu.org/gnu/wget/wget-latest.tar.gz
tar xvfz wget-latest.tar.gz
cd wget-1.11.3
./configure
sudo make install</pre>

<p>You've just compiled your first program. We just made a new directory for storing source code, downloaded wget's source, unzipped it, and then "made" the file with our XCode compiler. Pretty easy, right? The only catch is that you'll need your computer's administrator password to run the "sudo" command that will create wget's binary in your system folder.</p>

<p>In the future, that configure/make part is going to be the same for most of the source code you run into. When you encounter a new batch, just check the INSTALL or README docs where they'll usually let you know if there's anything else fancy you need to do.</p>

<p>Now test it out by hammering in the following...</p>

<pre lang="Bash">wget</pre>

<p>And there's your new utility, waiting to run things down on your behalf. Check out how it easy it is. Want to mirror a Web site? Here's all you need to type...</p>

<pre lang="Bash">wget -mk http://www.foo.com</pre>

<p>Blammo, you're off to the races, walking your target's directory structure and saving all the files to your hard drive. The -m option puts wget in mirror mode and the -k option will convert all the hyperlinks so they're suitable for local viewing. Then you just feed it the URL you're after.</p>

<p>If you're a Linux or Windows user, the command should be the same.  If you're a Windows user, you can try it with a release like <a href="http://users.ugent.be/~bpuype/wget/">this one</a>. And if you run Linux, like I do, wget should already be installed and ready to roll in most distributions. No bothering with XCode or new downloads or any of that nonsense.</p>