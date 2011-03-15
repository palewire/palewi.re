{% load media_url %}

var superSize = function() {
    $.fn.supersized.options = {  
        startwidth: 1024,  
        startheight: 683,
        vertical_center: 1,
        slides : [
            {image : '{% media_url "img/krs-1024x683.jpg" %}' }
        ]
    };
    $('#supersized').supersized();
}
var timeout = 2000;
var fire = "http://palewire.s3.amazonaws.com/bring_the_news_back/clip.wav"
var dropScience = function() {
    $.sound.play(fire);
    $("#content").append("<p>Bring the news back!</p>");
}
$(document).ready(function(){
    superSize();
    $("#content").queue("namedQueue", function() {
      dropScience();
      var self = this;
      setTimeout(function() {
        $(self).dequeue("namedQueue");
      }, timeout);
    });
    $("#content").queue("namedQueue", function() {
      var self = this;
      dropScience();
      setTimeout(function() {
        $(self).dequeue("namedQueue");
      }, timeout);
    });
    $("#content").queue("namedQueue", function() {
      var self = this;
      dropScience();
      setTimeout(function() {
        $(self).dequeue("namedQueue");
      }, timeout);
    });
    $("#content").queue("namedQueue", function() {
      var self = this;
      dropScience();
      setTimeout(function() {
        $(self).dequeue("namedQueue");
      }, timeout);
    });
    $("#content").dequeue("namedQueue");
    $("#content").click(dropScience);
});

