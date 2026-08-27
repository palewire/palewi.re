---
title: 'Django recipe: use extent of a queryset to set the zoom'
slug: django-recipe-use-extent-your-querset-set-map-zoom
published_at: '2009-08-13T19:09:27-07:00'
---
<p>Here's a fun trick from <a href="http://geodjango.org/">Django's geospatial extensions</a> that can come in
handy if you're ultimately displaying your points with a browser-based mapping system like <a href="http://openlayers.org/">
OpenLayers</a>.

<p>I sometimes find myself in a situation where I'd like the map to zoom in on a set of a points, but I'm not sure
ahead of time where those points will be. Imagine I have a database of all the hotdog stands in America&mdash;and a
tool that allows users to filter that set any number of ways, like state, county or address.</p>

<p>Here's a simple imaginary query.</p>

<pre lang="python">
>> from models import HotdogStand
>> queryset = HotdogStand.objects.filter(county='Johnson', state='Iowa')
</pre>

<p>Now here's the challenge: How can I write a OpenLayers template that will always center the map on my queryset, regardless
of what filter is applied, be it Johnson County, Iowa, or every point within 10 miles of Dodger Stadium.</p>

<p>I'm not sure I know the best way, but here's something I cooked up.</p>

<p>The function below accepts a queryset, along with its srid code. It grabs the queryset's extent and loads it
into an object. Then it converts that new object to srid 900913, the projection used by OpenLayers when displaying
Google Maps tiles, as I do on my sites.</p>

<pre lang="python">
from django.contrib.gis.geos import fromstr

def get_extent_for_openlayers(geoqueryset, srid):
    """
    Accepts a GeoQuerySet and SRID. 
    
    Returns the extent as a GEOS object in the Google Maps projection system favored by OpenLayers.
    
    The result can be directly passed out for direct use in a JavaScript map.
    """
    extent = fromstr('MULTIPOINT (%s %s, %s %s)' % geoqueryset.extent(), srid=srid)
    extent.transform(900913)
    return extent
</pre>

<p>The function can be called like so in a Django view.</p>

<pre lang="python">
>> from get_extent_for_openlayers import get_extent_for_openlayers
>> extent = get_extent_for_openlayers(queryset, 4326)
</pre>

<p>And then utilized as a dynamic method for setting the map's extent in your OpenLayers templates.</p>

<pre lang="javascript">
{% if extent %}
var wkt_f = new OpenLayers.Format.WKT();
var extent = wkt_f.read('{{ extent.wkt }}');
bounds = extent.geometry.getBounds();
map.zoomToExtent(bounds);
{% endif %}
</pre>

<p>Voilà. That's the whole trick. It seems to work for me, but if there's something I screwed up, feel free to tell me so.</p>