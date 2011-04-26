
			//sets up the close div button
			divtrigger("a#contract{{parent_title}}","div#expand_{{parent_title}}",'tag_contract/',{})
					
			$(document).ready(function(){
				//these first two highlight the target div when close is moused over
				$('#contract{{parent_title}}').mouseover(function(){
					$('div#expand_{{parent_title}}').addClass('div_hover');
				});
					         
				$('#contract{{parent_title}}').mouseout(function(){
					$('div#expand_{{parent_title}}').removeClass('div_hover');
				});
				
 				// Removes dotted line at top of tag branch weh n branch is closed
				$('#contract{{parent_title}}').click(function(){
					$('div#expand_{{parent_title}}').removeClass('div_hover');
					$('div#expand_{{parent_title}}').removeClass('toprule');
				});

			});
		