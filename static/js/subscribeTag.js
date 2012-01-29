
$(document).ready(function(){
	$('.subscribe_tag').each(function(){
		var data = $(this).metadata()
		var href = $(this).attr('href')
		var isAdd = new RegExp('add')
		var isAddTest = isAdd.test(href)
		if(isAddTest){
			$(this).replaceWith('<span class="button round subscribe_tag_span {tag:\''+data.tag+'\'}">Subscribe</span>')
		}
		else{
			$(this).replaceWith('<span class="button round subscribe_tag_span {tag:\''+data.tag+'\'}">Unsubscribe</span>')	
		}
	})
	$('.subscribe_tag_span').corner('40px')
		.click(function(){
			var data = $(this).metadata()
			if($(this).text()=='Subscribe'){
				$.ajax({
					type: "GET",
					url: "subscribe-tag/_add/"+data.tag+"/",	
				})
				$(this).text('Unsubscribe')
			}
			else{
				$.ajax({
					type: "GET",
					url: "subscribe-tag/_remove/"+data.tag+"/",	
				})
				$(this).text('Subscribe')	
			}
	})

})