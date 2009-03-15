	
	function slideBox () {
		$("#panel").slideToggle(1000);
		$(".btn-label-up").toggle();
		$(".btn-label-down").toggle();
		$(this).toggleClass("active"); 
		return false;
	}
	
	$(".btn-slide").click(function(){
		slideBox();
	});
	
	// Drop the box down and then up again as a tease.
	slideBox();
	slideBox();