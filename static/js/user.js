
$(document).ready(function(){
	$('.closeItem').click(function(event){
		event.preventDefault()
	})
	$('.closeItem').click(function(){
		var key = $(this).parent().attr('id')
		$.ajax({
			type: "POST",
			url: "/message/streamCancel/none/",
			data: 'key='+key,
			success: function(){				
				}
		})
		$(this).parent().remove()
	})	
})
