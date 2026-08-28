---
title: 'Django recipe: Twitter-style infinite scroll'
slug: django-recipe-twitter-style-infinite-scroll
published_at: '2010-11-07T12:36:59-08:00'
---
<p>Twitter added a cool feature. As you scroll down the page, more and more tweets are added to the bottom of the page. It creates an "infinite scroll" where you can read hundreds of tweets without having to click a single button. It's nice.</p>

<p>So, let's say you run a site that features a long list. And, let's say you'd like that list to automatically expand in the same way Twitter does. How would you make it happen?</p>

<p>I can't say I know the best way to do it, but I have a hacked out solution using <a href="http://docs.djangoproject.com/en/dev/topics/pagination/?from=olddocs">Django's pagination system</a> and <a href="http://jquery.com/">jQuery</a> with <a href="/applications/twitter-style-infinite-scroll-with-django-demo/" target="_blank">a demo posted here</a>. Here's what you need:</p>

<h2>01. A view that pulls the first page of data</h2>

<p>Mine passes out the latest tracks logged by palewire.com's robot massive.</p>

<pre lang="python">from django.views.generic.simple import direct_to_template
from django.core.paginator import Paginator, InvalidPage
from coltrane.models import Track

def newtwitter_pagination_index(request):
    """
    An index page where we can lay out how to pull off Twitter style
    pagination. 
    
    Passes out the 100 latest tracks to seed the page.
    """
    # Pull the data
    object_list = Track.objects.all()
    
    # Grab the first page of 100 items
    paginator = Paginator(object_list, 100)
    page_obj = paginator.page(1)
    
    # Pass out the data
    context = {
        "object_list": page_obj.object_list,
        "page": page_obj,
    }
    template = 'newtwitter_pagination/index.html'
    return direct_to_template(request, template, context)</pre>

<h2>02. An HTML template that lays out the list</h2>

<p>Here's the part where I place the object_list pulled above. Notice how it has that anchor div at the end. We'll use that later.</p>

<pre lang="html"><ul class="newtwitter">
    {% for object in object_list %}
    <li>
        <a href="{{ object.url }}">
        {{ object.pub_date|date:"U" }}:&nbsp;&nbsp;&nbsp;{{ object|truncatewords:10 }}
        </a> 
    </li>
    {% endfor %}
    <div id="newtwitter-anchor"></div>
</ul>
</pre>

<h2>03. A view that pulls any page and serves it as JSON</h2>

<p>My view looks like this:</p>

<pre lang="python">def newtwitter_pagination_json(request, page):
    """
    A JSON feed to feed updates to the index page as the user
    scrolls down the page. 
    
    Passes out pages of Track objects based on the `page` kwarg.
    """
    # Pull the data
    object_list = Track.objects.all()
    
    # Pull the proper items for this page
    paginator = Paginator(object_list, 100)
    try:
        page_obj = paginator.page(page)
    except InvalidPage:
        # Return 404 if the page doesn't exist
        raise Http404
    
    # Pass out the data
    context = {
        "object_list": page_obj.object_list,
        "page": page_obj,
    }
    template = 'newtwitter_pagination/tracks.json'
    return direct_to_template(request, template, context, 'text/javascript')</pre>

<p>It hooks up to the JSON template like this. Don't worry about the special templatetags. All they do is help clip the string.</p>

<pre lang="javascript">{{% load coltrane_tags %}
    "page": {{ page.number }},
    "hasNext": {{ page.has_next|lower }},
    "itemList": [{% for obj in page.object_list %}
        {"string": "{{ obj.pub_date|date:"U" }}:&nbsp;&nbsp;&nbsp;{{ obj|truncatewords:10|escapejs }}", "url": "{{ obj.url }}"}{% if not forloop.last %},{% endif %}{% endfor %}
    ]
}</pre>

<p>The two views are wired to urls that look like this.</p>

<pre lang="python">from django.conf.urls.defaults import *
from coltrane import views

urlpatterns = patterns('',
    
    # newtwitter style autopagination with django
    url(r'^twitter-style-infinite-scroll-with-django-demo/$',
        views.newtwitter_pagination_index,
        name='coltrane_app_newtwitter_index'),
    
    url(r'^twitter-style-infinite-scroll-with-django-demo/json/(?P<page>[0-9]+)/',
        views.newtwitter_pagination_json,
        name='coltrane_app_newtwitter_json')
)</pre>

<h2>04. JavaScript that loads JSON, is hooked to scroll event</h2>

<p>There's a function in the head of <a href="/applications/twitter-style-infinite-scroll-with-django-demo/">the demo</a> that hits the JSON view and loads the data as list items just above our anchor div. It's called loadItems below.</p>

<p>It's hooked to the scroller using jQuery's $(window).bind() function. The decision on when to trigger an update is handled in that loadOnScroll function which checks the current position of the scroller against the cutoff I've put in.</p>

<p>You can adjust where that is by increasing or decreasing the number 3 I tossed in there. That works okay for this site, which has a small footer, but you might want a bigger or smaller one depending on your site's design.</p>

<p>The scroll handler is wired up in the $(document).ready() bit at the end there.</p>

<pre lang="javascript">// Scroll globals
var pageNum = {{ page.number }}; // The latest page loaded
var hasNextPage = {{ page.has_next|lower }}; // Indicates whether to expect another page after this one
var baseUrl = '{% url coltrane_app_newtwitter_index %}'; // The root for the JSON calls

// loadOnScroll handler
var loadOnScroll = function() {
   // If the current scroll position is past out cutoff point...
    if ($(window).scrollTop() > $(document).height() - ($(window).height()*3)) {
        // temporarily unhook the scroll event watcher so we don't call a bunch of times in a row
        $(window).unbind();
        // execute the load function below that will visit the JSON feed and stuff data into the HTML
        loadItems();
    }
};

var loadItems = function() {
    // If the next page doesn't exist, just quit now 
    if (hasNextPage === false) {
        return false
    }
    // Update the page number
    pageNum = pageNum + 1;
    // Configure the url we're about to hit
    var url = baseUrl + "json/" + pageNum + '/';
    $.ajax({
        url: url, 
        dataType: 'json',
        success: function(data) {
            // Update global next page variable
            hasNextPage = data.hasNext;
            // Loop through all items
            var html = [];
            $.each(data.itemList, function(index, item){
                /* Format the item in our HTML style */
                html.push('<li><a href="', item.url, '">', item.string, '</a></li>')
            });
            // Pop all our items out into the page
            $("#newtwitter-anchor").before(html.join(""));
        },
        complete: function(data, textStatus){
            // Turn the scroll monitor back on
            $(window).bind('scroll', loadOnScroll);
        }
    });
};

$(document).ready(function(){     
   $(window).bind('scroll', loadOnScroll);
});
</pre>

<p>And that's pretty much all the moving parts. Obviously, not rocket science. And hardly innovative on my part. There are much more sophisticated implementations <a href="http://code.google.com/p/django-endless-pagination/">here</a> and <a href="http://www.infinite-scroll.com/">here</a> that I glanced at before deciding to hack out what's above. The loadOnScroll handler is my perversion of what I found open-sourced in <a href="http://code.google.com/p/django-endless-pagination/">django-endless-pagination</a>. If you see anything that sucks, let me know in the comments below.</p>