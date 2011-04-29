/*

*/

//include tiny mce in textareas when pages render
//still needs to be independently loaded with ajaxed forms
function basic_MCE()
	{
		tinyMCE.init({
		        mode : "textareas",
			    theme : "advanced",
			    plugins: "lists",
			    theme_advanced_buttons1 : "bold,italic,underline,strikethrough,|,link,unlink,|,bullist, numlist,|,blockquote,undo", 
			    theme_advanced_buttons2 : "", 
			    theme_advanced_buttons3 : "" ,
			    theme_advanced_statusbar_location : "bottom",
			    theme_advanced_resizing : true
		});			    
	}

		
// shorthand for a .load into a div using an optional confirmation
function divtrigger(trigger,div,url,context,confirm_message)
		{
			$(document).ready(function(){
				$(trigger).click(function(){
					if (confirm_message == null) 
						{
							var confirmation= true;
						}
					else 
						{
							var confirmation = confirm(confirm_message);
						};
					if (confirmation==true)
					
						{
							$(div).load(
								url,
								context
							);
						};
				});
			});	
		}	
		
//this confirm is for forms and urls
function confirmSubmit(message)
	{
	var agree=confirm(message);
	if (agree)
		return true ;
	else
		return false ;
	}

function array_member(array, element)
	{
		for (i=0;i<array.length;i++)
			{
				if (array[i] == element)
				{
					return true
				}
			}
		return false
	}
	
function array_remove(array, element)
	{
		for (i=0;i<array.length;i++)
			{
			if (array[i] == element)
				{
					array.splice(i,1);
				}
			}
		return array;
	}
	
basic_MCE()
