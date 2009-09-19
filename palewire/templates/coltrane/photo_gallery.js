
		// Initialize Advanced Galleriffic Gallery
		var galleryAdv = $('#gallery').galleriffic('#thumbs', {
			delay:                  2000,
			numThumbs:              12,
			preloadAhead:           10,
			enableTopPager:         false,
			enableBottomPager:      false,
			imageContainerSel:      '#slideshow',
			loadingContainerSel:    '#loading',
			renderSSControls:       false,
			renderNavControls:      false,
			enableHistory:          false,
			autoStart:              false,
			onChange:               function(prevIndex, nextIndex) {
				$('#thumbs ul.thumbs').children()
					.eq(prevIndex).fadeTo('fast', onMouseOutOpacity).end()
					.eq(nextIndex).fadeTo('fast', 1.0);
			},
			onTransitionOut:        function(callback) {
				$('#slideshow').fadeTo('fast', 0.0, callback);
			},
			onTransitionIn:         function() {
				$('#slideshow').fadeTo('fast', 1.0);
			},
			onPageTransitionOut:    function(callback) {
				$('#thumbs ul.thumbs').fadeTo('fast', 0.0, callback);
			},
			onPageTransitionIn:     function() {
				$('#thumbs ul.thumbs').fadeTo('fast', 1.0);
			}
		});

