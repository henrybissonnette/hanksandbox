/*
 * Replace scripless submit 
 * remove scriptless hidden
 * 
 * */

basic_MCE()

var added_tags = new Array();


$(document).ready(function(){
	
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
	
			if (array_member(works,x))
				{
					var confirmation = confirm("You have already created a document with this file name. Do you want to replace it?");
					return confirmation;
				}
		}
		
		$('form').submit(function(){
				return validateFilename(works)
			})
		
	}
	// load tag manager into a div
	$('button#browse_tags').click(function(){
		$('div#tags').load(
						'tag_base/',
						{"user_type":"user"}
						);
	});	
	
	// replace the text of the scriptless submit button
	$('form input[value="Next Step: Add Tags >>"]').attr('value','Create')
	
})
