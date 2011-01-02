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
var dropScience = function() {
    var soundfile = "http://palewire.s3.amazonaws.com/bring_the_news_back/clip.wav"
    $.sound.play(soundfile);//, {'timeout': 0});
    //$("#content").html("<p>Bring the news back!</p>");
}
$(document).ready(function(){
    superSize();
    dropScience();
});
