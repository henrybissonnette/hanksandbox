

/* DOCUMENT RATING SYSTEM */
$(document).ready(function(){
	$('#document_info form[action="/rate/"]').submit(function(event){
		event.preventDefault()
	})
	$('#document_info form[action="/rate/"] input[type="submit"]').click(function(){
		var rating = $(this).siblings('input[name="rating"]').val()
		var key = $(this).siblings('input[name="key"]').val()
		$.ajax({
			type: "POST",
			url: "/ajax/rate/",
			data: 'key='+key+'&rating='+rating,
			success: function(currentRating){
				$('#document_info form[action="/rate/"]').replaceWith('<span class="rate">Thanks for rating this document.</span>')
				$('#document_info #rating').html('Rating: '+currentRating)
				}
		})
	})

})	




