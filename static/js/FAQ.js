basic_MCE()

$(document).ready(function(){
	$('div#index').remove()
	$('div.answer').hide()
	$('div.nested').hide()
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
