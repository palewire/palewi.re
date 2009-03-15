
{% load coltrane_tags %}
{% get_all_slogans %}

		// An array of palewire slogans
		var slogans = [
			{% for slogan in slogan_list %}'{{ slogan }}',{% endfor %}
		];
	
		// Pulls a random item from an array
		var random_item = function ( array ) {
			var n = array.length;
			return array[(Math.floor(Math.random() * n))];
		};
	
		// Add randomly selected slogans
		$('#hd h1').append('<span class="slogan" title="slogan">' + random_item(slogans) + '<\/span>');
	
		// Add titles for link buttons
		jQuery.each($("#navbar a"), function() {
			var title = $( this ).attr("title");
			$('#hd h1').append('<span class="icon" title="'+ title + '">'+ title +'<\/span>');
		});
		
		// Hide newly created link titles
		$('#hd span').hide()
	
		// Show slogan on mouseover
		$('#hd h1').mouseover(function(){
			$('#hd span[title=slogan]').show();
			})

		// Hide slogan on mouseoff
		$('#hd h1').mouseout(function(){
			$('#hd span[title=slogan]').hide();
			})

		// Show link title on mouseover
		$('#navbar a').mouseover(function(){
			var title = $(this).attr('title');
			$('#hd span[title='+title+']').show();
			})
		
		// Hide link title on mouseoff
		$('#navbar a').mouseout(function(){
			var title = $(this).attr('title');
			$('#hd span[title='+title+']').hide();
			})