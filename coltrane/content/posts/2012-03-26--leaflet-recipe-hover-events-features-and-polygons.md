---
title: 'Leaflet recipe: hover events on features and polygons'
slug: leaflet-recipe-hover-events-features-and-polygons
published_at: '2012-03-26T13:47:10-07:00'
---
<p>Leaflet is an exciting tool for making interactive maps. It's free. It's simple. It's easy to write. It isn't tied to any one set of background tiles. It works in all the major browsers. It's under <a href="https://github.com/CloudMade/Leaflet">active development</a>.</p>

<p>It even has <a href="http://leaflet.cloudmade.com/examples.html">good documentation</a>. But one thing it doesn't show you how to create is hover effects. Say you've got some shapes or points on your map and you want something to happen when the user rolls her mouse over them. After getting <a href="https://github.com/CloudMade/Leaflet/issues/60">some help from GitHubber patmisch</a>, here's how I made it work.</p>

<h2>Getting started</h2>

<p>The city of Los Angeles recently redrew its City Council districts. Below is a Leaflet map displaying the boundaries from the redistricting commission's final recommendation. I downloaded the lines as a <a href="http://en.wikipedia.org/wiki/Shapefile">shapefile</a> from <a href="http://redistricting2011.lacity.org/LACITY/proposedFinalMap.html">the commission's Web site</a> and converted them into <a href="http://en.wikipedia.org/wiki/GeoJSON">GeoJSON</a> format using <a href="http://en.wikipedia.org/wiki/Qgis">Quantum GIS</a>.</p>

<iframe src="http://s3-us-west-1.amazonaws.com/palewire/leaflet-hover/before.html" frameborder=0 scrolling=no width=100% height=350px></iframe>

<p style="margin-top:10px">This kind of map can be accomplished by following the <a href="http://leaflet.cloudmade.com/examples/geojson.html">GeoJSON instructions</a> Leaflet already provides. One hundred percent of the code is below. I've annotated it to provide some clues to what's happening, but this is the baseline for making a static map run and I'm going to assume you get how it works. If you get stuck up, fire off a question in the comments or spend some time with <a href="http://leaflet.cloudmade.com/index.html">Leaflet's tutorial for beginners</a>.</p>

<pre lang="html">
<!DOCTYPE html>
<html>
<head>
    <title>Leaflet GeoJSON example</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- All the stuff you need to install from Leaflet -->
    <link rel="stylesheet" href="http://cdn.leafletjs.com/leaflet-0.4/leaflet.css" />
    <!--[if lte IE 8]><link rel="stylesheet" href="http://cdn.leafletjs.com/leaflet-0.4/leaflet.ie.css" /><![endif]-->
    <script src="http://cdn.leafletjs.com/leaflet-0.4/leaflet.js"></script>
    <!-- My external GeoJSON file with the City Council boundaries in it -->
    <script src="http://s3-us-west-1.amazonaws.com/palewire/leaflet-hover/citycouncil.geojson"></script>
</head>
<body style="margin:0; padding:0;">
    <!-- The <div> where we're put the map -->
    <div id="map" style="width: 100%; height: 350px;"></div>
    <script type="text/javascript">
        // Initialize the map object
        var map = new L.Map('map', {
            // Some basic options to keep the map still and prevent 
            // the user from zooming and such.
            scrollWheelZoom: false,
            touchZoom: false,
            doubleClickZoom: false,
            zoomControl: false,
            dragging: false
        });
        // Prep the background tile layer graciously provided by stamen.com
        var stamenUrl = 'http://{s}.tile.stamen.com/toner/{z}/{x}/{y}.png';
        var stamenAttribution = 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC BY SA</a>.';
        var stamenLayer = new L.TileLayer(stamenUrl, {maxZoom: 18, attribution: stamenAttribution});
        // Set the center on our city of angels
        var center = new L.LatLng(34.0, -118.4);
        map.setView(center, 9);
        // Load the background tiles
        map.addLayer(stamenLayer);
        // Create an empty layer where we will load the polygons
        var featureLayer = new L.GeoJSON();
        // Set a default style for out the polygons will appear
        var defaultStyle = {
            color: "#2262CC",
            weight: 2,
            opacity: 0.6,
            fillOpacity: 0.1,
            fillColor: "#2262CC"
        };
        // Define what happens to each polygon just before it is loaded on to
        // the map. This is Leaflet's special way of goofing around with your
        // data, setting styles and regulating user interactions.
        var onEachFeature = function(feature, layer) {
            // All we're doing for now is loading the default style. 
            // But stay tuned.
            layer.setStyle(defaultStyle);
        };
        // Add the GeoJSON to the layer. `boundaries` is defined in the external
        // GeoJSON file that I've loaded in the <head> of this HTML document.
        var featureLayer = L.geoJson(boundaries, {
            // And link up the function to run when loading each feature
            onEachFeature: onEachFeature
        });
        // Finally, add the layer to the map.
        map.addLayer(featureLayer);
    </script>
</body>
</html>
</pre>

<h2>Hooking up hovers</h2>

<p>Our goal is to make the same map as above, except with polygons that light up on hover and a popup that appears with metadata about the selected council district. Something like this.</p>

<iframe src="http://s3-us-west-1.amazonaws.com/palewire/leaflet-hover/after.html" frameborder=0 scrolling=no width=100% height=350px></iframe>

<p style="margin-top:10px;">First add jQuery to the head of the page, so we can easily make the popup when the time comes.</p>

<pre lang="html"><script src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js"></script>
</pre>

<p>Then create a second style set that describes how to brighten up the polygon.</p>

<pre lang="javascript">var highlightStyle = {
    color: '#2262CC', 
    weight: 3,
    opacity: 0.6,
    fillOpacity: 0.65,
    fillColor: '#2262CC'
};</pre>

<p>Now the real work. Look back at how we used the "featureparse" event above to assign the default style to each polygon. You can assign events in the same way, turning them on one at a time as Leaflet loops through your GeoJSON features and adds them to the layer. The only trick is to bind your events using a <a href="http://www.hunlock.com/blogs/Functional_Javascript#quickIDX5">self-invoking function</a> that gets the scope right and lines things up as they loop by.</p>

<p>Watch as it happens below. The wrapper function passes in the layer and JSON metadata, which are then assigned as the function is executed before each step of the loop is complete.</p>

<pre lang="javascript">var onEachFeature = function(feature, layer) {
    // Load the default style. 
    layer.setStyle(defaultStyle);
    // Create a self-invoking function that passes in the layer
    // and the properties associated with this particular record.
    (function(layer, properties) {
      // Create a mouseover event
      layer.on("mouseover", function (e) {
        // Change the style to the highlighted version
        layer.setStyle(highlightStyle);
        // Create a popup with a unique ID linked to this record
        var popup = $("<div></div>", {
            id: "popup-" + properties.DISTRICT,
            css: {
                position: "absolute",
                bottom: "85px",
                left: "50px",
                zIndex: 1002,
                backgroundColor: "white",
                padding: "8px",
                border: "1px solid #ccc"
            }
        });
        // Insert a headline into that popup
        var hed = $("<div></div>", {
            text: "District " + properties.DISTRICT + ": " + properties.REPRESENTATIVE,
            css: {fontSize: "16px", marginBottom: "3px"}
        }).appendTo(popup);
        // Add the popup to the map
        popup.appendTo("#map");
      });
      // Create a mouseout event that undoes the mouseover changes
      layer.on("mouseout", function (e) {
        // Start by reverting the style back
        layer.setStyle(defaultStyle); 
        // And then destroying the popup
        $("#popup-" + properties.DISTRICT).remove();
      });
      // Close the "anonymous" wrapper function, and call it while passing
      // in the variables necessary to make the events work the way we want.
    })(layer, feature.properties);
};</pre>

<p>That's it. If this doesn't make sense, or I've made a mistake, please leave a comment below. You can find the source code for the complete working demo <a href="http://s3-us-west-1.amazonaws.com/palewire/leaflet-hover/after.html">here</a>.</p>