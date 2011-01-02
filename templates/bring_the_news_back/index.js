{% load media_url %}
    $(document).ready(function(){
        $(function(){
            $.fn.supersized.options = {  
                startwidth: 1024,  
                startheight: 683,
                vertical_center: 1,
                slides : [
                    {image : '{% media_url "img/krs-1024x683.jpg" %}' }
                ]
            };
            $('#supersized').supersized();
            var soundfile = "http://palewire.s3.amazonaws.com/bring_the_news_back/clip.mp3"
            $.sound.play(soundfile);
        });
    });
