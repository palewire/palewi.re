		
	$(".btn-slide").click(function(){
		$("#panel").slideToggle("slow");
		$(".btn-label-up").toggle();
		$(".btn-label-down").toggle();
		$(this).toggleClass("active"); 
		return false;
	});
