	
	var added_tags = new Array();
	

$(document).ready(function(){	
	var doc = $('h1.document').metadata()
	
	$('.tagButton').each(function(){
		added_tags.push("'"	+$(this).attr('value')+"'"	)
	})
	function confirmSubmit(message)
	{
	var agree=confirm(message);
	if (agree)
		return true ;
	else
		return false ;
	}
	
	basic_MCE()
			
	$('#favorite').click(function(){	
												
			$.ajax({
				type: "POST",
				url: document.URL+"favorite/",
				success: function(){
					$('#favorite_div').ajaxComplete(function(event,request,settings){
						$(this).html('This document is now one of your favorites!')				
					})
				}
			})				
	})

	$("a.rate_up").click(function(){
		$("div#rate").load('rate/',{
			"rating":"up",
			"filename":doc.filename,
			"username":doc.author,
			});
	});
	$("a.rate_down").click(function(){
		$("div#rate").load('rate/',{
			"rating":"down",
			"filename":doc.filename,
			"username":doc.author,
			});
	});
	


	
	//the following two items validate filenames
	$.ajax({
			type: "GET",
			url: "/ajax/getWorks/",
			success: function(data){
				userWorks = eval('('+data+')')
				setValidator(userWorks.works)
			}
	})
					
	var setValidator = function(works){
				
		var validateFilename = function(works){
			var forbidden = "`~!@#$%^&*()+={}[]\\|:;\"\'<>,. ";
			var x=document.getElementById("filename").value;
			
			if (x==null || x=="")
			  {
				  alert("Filename is required.");
				  return false;
			  }
			for(i=0;i < forbidden.length;i++)
				{
					if (x.indexOf(forbidden.charAt(i)) != -1)
					{
						alert("Filenames may only contain a-z, A-Z, 1-9, _ , and -.");
						return false;
					}
				}
	
			if (array_member(works,x) && x != doc.filename)
				{
					var confirmation = confirm("You have already created a document with this file name. Do you want to replace it?");
					return confirmation;
				}
		}
		
		$('form[action="/create"]').submit(function(){
				return validateFilename(works)
			})
		
	}
	// load tag manager into a div
	$('button#browse_tags').click(function(){
		$('div#tags').load(
						'tag_base/',
						{"user_type":"user"}
						)
	});	
	
	
	$('#cancel_button').click(function(){
			var agree=confirm('You are about to close this document without saving. Continue?');
			if (agree)
				window.history.back();
		})
		
	$('form[action="delete/"]').submit(function(){
		return confirmSubmit('Do you want to permanently delete this document?')
	})
	
	/*divtrigger("button#browse_tags","div#tags",'tag_base/',{"user_type":"user"})
	
				$(document).ready(function(){
				
				for(var i=0;i<added_tags.length;i++){
					
					var context = [['title',added_tags[i].slice(1,-1)]]
					temp_string = 	'<div class="include_%title%">	\
									<input type="hidden" name="added_tag" class="include_%title%" value="%title%"/>	\
									</div>'
					var final_string = template(temp_string,context);
					$('input#create_input').after(final_string);
				}
			})
		*/
			
})	
						

