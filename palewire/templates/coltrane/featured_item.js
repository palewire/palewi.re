	
	function slideBox () {
		$(".btn-label-up").toggle();
		$(".btn-label-down").toggle();
		$("#panel").slideToggle(1000);
		$(this).toggleClass("active"); 
		return false;
	}
	
	$(".btn-slide").click(function(){
		slideBox();
	});
	
	// Drop the box down and then up again as a tease.
	slideBox();
	slideBox();