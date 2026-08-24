---
title: 'Django recipe: Dynamically load a Google Maps API key'
slug: django-recipe-dynamically-load-your-google-maps-api-key
published_at: '2009-10-29T18:06:46-07:00'
---
<p>So here's the situation. You've got a <a href="http://www.djangoproject.com/">Django</a> app that uses the <a href="http://code.google.com/apis/maps/">Google Maps API</a>. 
	And you want to deploy the HTML across multiple domains&mdash;like development, staging and production environments.
	</p>

<p>Typically, you call Google's Mapping API with your registered API key.</p>

<pre lang="html">
<script src="http://maps.google.com/maps?file=api&amp;v=2&amp;key=ABQIAAAAE7jH76TvSwj2EbGtTFztGBSZQPaKzcJUNBmscSu8lUTMp7T2MxRd9I3aSZGU4Qk1Ibht_Cu0cZYCqQ" type="text/javascript"></script>
</pre>

<p>But, in this scenario, each of your domains may require a different Google API key. 
	Which means you can't just paste the key directly into your HTML template and use it
	across the board, because it will only work for the one domain where it's registered.
</p>

<p>Here's my workaround. Create a <a href="http://www.b-list.org/weblog/2006/jun/14/django-tips-template-context-processors/">
	context processor</a> that will dynamically select your API key depending on the domain, and 
	automatically pump it into your template so it's always ready for you to call. 
<p>
	
<p>So, instead of pasting in the whole key, like we did above. You end up doing something like this.</p>

<pre lang="html">
<script src="http://maps.google.com/maps?file=api&amp;v=2&amp;key={{ gmaps_api_key }}" type="text/javascript"></script>
</pre>

<p>How's it done? Well, I created a folder in my utilities folder, called context_processors, where I made a new file
	named api_keys.py. Here it is.</p>

<pre lang="python">
def gmaps(request):
    """
    Pulls the Google Maps API key depending on the current domain.
    """
    domain2key = {
        'dev.palewire.com': 'ABQIAAAAE7jH76TvSwj2EbGtTFztGBR8UkcbL4-dL61bzErP2SNv1WNIGBQvXvskpcbuLQTIG7VNcEyd_E-oAA',
        'stage.palewire.com': 'ABQIAAAAE7jH76TvSwj2EbGtTFztGBSO5LlXme5quZiFrf4fQnu-lsRFhBR1f1qhogtXJLk5oZTcBn8Gty3MPQ',
        'www.palewire.com': 'ABQIAAAAE7jH76TvSwj2EbGtTFztGBSZQPaKzcJUNBmscSu8lUTMp7T2MxRd9I3aSZGU4Qk1Ibht_Cu0cZYCqQ',
    }
    try:
        server_name = request.META['HTTP_HOST']
        key = domain2key[server_name]
    except KeyError:
        key = domain2key['www.palewire.com']

    return {'gmaps_api_key': key }
</pre>

<p>First I made a dictionary that crosswalks between my domains and their Google API keys.</p>

<p>Then the code pulls the host from the current request (for a full list of attributes in the request object, visit <a href="http://docs.djangoproject.com/en/dev/ref/request-response/#httprequest-objects">the Django docs</a>), and checks the dictionary to see whether there's a key for that domain.</p>

<p>If it finds one, it passes
	it out in a variable called gmaps_api_key. If it doesn't find a key for the domain, it defaults to the key for
	the production environment at www.palewire.com.
</p>

<p>Before it will work, you'll need to add the file to the context processors list in your settings.py. Mine looks like this.</p>

<pre lang="python">
    TEMPLATE_CONTEXT_PROCESSORS = (
        'toolbox.context_processors.api_keys.gmaps',
        'django.core.context_processors.auth',
        'django.core.context_processors.debug',
        'django.core.context_processors.i18n',
        'django.core.context_processors.media',
        'django.core.context_processors.request',
    )
</pre>

<p>And, don't forget this part, you need to make sure that you're using a view that actually uses the context processors. 
	Generic views will do it by default, but <a href="http://docs.djangoproject.com/en/dev/topics/http/shortcuts/#render-to-response">render_to_response</a> won't.
</p>

<p>
	Because of that shortcoming in render_to_response, I've switched to using the <a href="http://docs.djangoproject.com/en/dev/ref/generic-views/#django-views-generic-simple-direct-to-template">direct_to_template</a> 
	generic view instead. The only additional code necessary is to include the request in your call, like so.
</p>

<pre lang="python">
# So start doing this...
direct_to_template(request, 'my_app/template.html', {'object_list': object_list})
# And stop doing this...
render_to_response('my_app/template.html', {'object_list': object_list})
</pre>

<p>That's the whole trick. Per usual, feel free to tell me where I screwed up in the comments. We'll sort it out.</p>