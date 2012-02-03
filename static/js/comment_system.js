/********************************************************
 * This script enhances the comment system. It adds hiding
 * and revealing of comments, as well as AJAX loading of 
 * comment, reply, and edit forms.
 *******************************************************/

/*MINIMIZE/MAXIMIZE*/

$(document).ready(function(){  
$('.commentBox').corner('bottom');
$('.comment .header').css('cursor','pointer').corner('top');
$('.comment .content').corner("round bottom 8px").parent().corner("round bottom 10px")
	
$(".comment .header").toggleClass("commentHeaderMax");
$(".comment .header").click(function () { 
	if($(this).hasClass("commentHeaderMax")){
			comment = $(this).next().children('.comment .content')
			$(this).append('<span class="stub">:     '+comment.text()+'</span>');
			$(this).siblings('form, button').hide(function(x){$(x).corner();}(this));
			$(this).next().slideUp('fast'); 			
		}
	else{
			$(this).children('span.stub').remove()
			$(this).next().slideDown(); 
			$(this).siblings('form, button').slideDown();
			$(this).uncorner().corner('top');
	}
		$(this).toggleClass('commentHeaderMax');
		$(this).toggleClass('commentHeaderMin');
		
	});
})

/*COMMENT BOXES*/


$(document).ready(function(){
	
	$('form[action="/postcomment/"]').submit(function(event){
		event.preventDefault()
		var commentData = {}
		var subscribeCheck
		if ($('input[type="submit"]', this).val()=="Reply"){
			commentData['subjectValue']='Re: '+ $(this).siblings('.header').children('.subject').text()
			commentData['aboveKeyValue']=$('input[name="aboveKey"]', this).val()
			commentData['submitValue']='Reply'	
		}
		if ($('input[type="submit"]', this).val()=="Post Comment"){
			commentData['subjectValue']='Re: '+$('title').text()
			commentData['aboveKeyValue']=$('input[name="aboveKey"]', this).val()
			commentData['submitValue']='Post Comment'	
		}
		if ($('input[type="submit"]', this).val()=="Edit"){
			commentData['subjectValue']=$(this).siblings('.header').children('.subject').text()
			commentData['selfKeyValue']=$('input[name="selfKey"]', this).val()
			commentData['contentValue']=$(this).siblings('.commentBox').children('.comment .content').html()
			commentData['submitValue']='Save'				
			commentData['subscribeChecked']=subscribeCheck

		}
		var myHank = new hank
		var commentForm = myHank.createCommentBox(commentData)

		$(this).hide().after(commentForm)
		basic_MCE()
		$('.postcomment').corner()
		$('.postcomment .exit').click(function(){
			$(this).parent().prev().show()
			$(this).parent().remove()
		})
		
		//CHECK SUBSCRIPTION PREFERENCE
		if ($('input[type="submit"]', this).val()=="Edit"){
			function retrieveAjax(isSubscribed){
				if(isSubscribed == 'true'){
					$('#comment'+commentData.selfKeyValue+' input[name="subscribe"]').attr('checked','checked')
				}
				else{
					$('#comment'+commentData.selfKeyValue+' input[name="subscribe"]').removeAttr('checked')
				}
			}

			$.ajax({
				type: "POST",
				url: "/ajax/subscribe-query/",
				data: "selfKey=" + commentData['selfKeyValue'],
				success: function(isSubscribed){
				retrieveAjax(isSubscribed)
				}
			})				

	
			//DELETION
			$('input[value="Delete"]').click(function(){
				selfKey = $(this).siblings('input[name="selfKey"]').val()
				if(confirm('This comment will be permanently deleted.')){
					$.ajax({
						type: "POST",
						url: "/ajax/delete-comment/",
						data: "selfKey=" + selfKey,
						success: function(){
							if ($('.comment#'+selfKey).next().hasClass('nested')){
								$('.comment#'+selfKey).next().remove()
							}
							$('.comment#'+selfKey).remove()
						}
					})						
				}
			})
		}		
	})
	
})

/* RATING SYSTEM */
$(document).ready(function(){
	$('.commentBox form[action="/rate/"]').submit(function(event){
		event.preventDefault()
	})
	$('.commentBox form[action="/rate/"] input[type="submit"]').click(function(){
		var rating = $(this).siblings('input[name="rating"]').val()
		var key = $(this).siblings('input[name="key"]').val()
		$.ajax({
			type: "POST",
			url: "/ajax/rate/",
			data: 'key='+key+'&rating='+rating,
			success: function(currentRating){
				$('.comment#'+key+' .commentBox form[action="/rate/"]').replaceWith('<span class="rate">Thanks for rating this comment.</span>')
				$('.comment#'+key+' .header .commentRating').html('(Rating: '+currentRating+')')
				}
		})
	})
})

/* RATING THRESHOLD */

$(document).ready(function(){
	var threshold = $('.threshold').attr('value')
	$('.comment').each(function(){
				if ($('.commentRating',this).attr('value') < threshold){
					$('.header',this).trigger('click')
				}		
			})
})
