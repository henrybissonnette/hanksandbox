basic_MCE()

$(document).ready(function(){
	$('div#index').remove()
	$('div.answer').hide()
	/*$('div.nested').hide()    once there's a lot more content this may make sense*/
	$('h2').css('cursor','pointer').each(function(){
		$(this).click(function(){
			$(this).nextAll('div.nested').toggle()
		})
	})
	$('h3.question').css('cursor','pointer').each(function(){
		$(this).click(function(){
			$(this).next().toggle()
		})
	})
})
