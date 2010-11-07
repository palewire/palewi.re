// Scroll globals
var pageNum = {{ page.number }};
var hasNextPage = {{ page.has_next|lower }};
var loadInProgress = false;
var baseUrl = '{% url coltrane_app_newtwitter_index %}';

// loadOnScroll handler
var loadOnScroll = function() {
    if ($(window).scrollTop() > $(document).height() - ($(window).height()*3)) {
        $(window).unbind();
        loadItems();
    }
};

// loadOnScroll action
var loadItems = function() {
    // If the next page doesn't exist, just quit now 
    if (hasNextPage === false) {
        return false
    }
    // Update the page number
    pageNum = pageNum + 1;
    // Configure the url we're about to hit
    var url = baseUrl + "json/" + pageNum + '/';
    $.ajax({
        url: url, 
        dataType: 'json',
        success: function(data) {
            // Update global next page variable
            hasNextPage = data.hasNext;
            // Loop through all items
            var html = [];
            $.each(data.itemList, function(index, item){
                /* Format the item in our HTML style */
                html.push('<li>', item.string, '</li>')
            });
            // Pop all our items out into the page
            $("#newtwitter-anchor").before(html.join(""));
        },
        complete: function(data, textStatus){
            // Close out the loading variable 
            loadInProgress = false;
            // Turn the scroll monitor back on
            $(window).bind('scroll', loadOnScroll);
        }
    });
};



