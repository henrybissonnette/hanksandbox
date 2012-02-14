
//include tiny mce in textareas when pages render
//still needs to be independently loaded with ajaxed forms
function basic_MCE()
	{		
		tinyMCE.init({
				
		        mode : "textareas",
			    theme : "advanced",
			    plugins: "lists,paste"/*,tinyautosave"*/,
			    content_css : "/static/css/custom_content.css",
			    
            	paste_auto_cleanup_on_paste : true,
            	paste_remove_styles: true,
            	paste_remove_styles_if_webkit: true,
            	paste_strip_class_attributes: true,
			            
			    theme_advanced_buttons1 : /*"tinyautosave,|,"*/"bold,italic,underline,strikethrough,|,link,unlink,|,bullist, numlist,|,blockquote,undo,|,formatselect,charmap", 
			    theme_advanced_buttons2 : "", 
			    theme_advanced_buttons3 : "" ,
			    theme_advanced_statusbar_location : "bottom",
			    theme_advanced_resizing : true,
			    theme_advanced_blockformats : "h3",
			    
			    gecko_spellcheck : true,
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
	
//clicking on 'controller' reveals 'revealed'. Both should be strings.	
//initial state is visible if 'hidden' = false
function reveal_controller(controller, element, hidden)
	{
		
		$(document).ready(function(){
			$(controller).addClass('clickable menu_head')
			if (hidden === false){}
			else
			{
				$(element).hide();
			}
			
			$(controller).click(function(){
				if ($(element).is(":visible"))
				{
					$(element).hide();
				}
				else
				{
					$(element).show();
				}
				
			})
		})
	}
	
function tabular(controller, element, groupname ,initial)
	{
		$(document).ready(function(){
			if(initial){
				$(controller).addClass('selected')
			}
			else{
				$(controller).addClass('unselected')
				$(element).hide();
			}
			$(controller).addClass(groupname+' tab');
			$(element).addClass(groupname+' tabbed');
			$('.tab').corner('top')
			$(controller).click(function(){
				$('.selected.'+groupname).addClass('unselected');
				$('.selected.'+groupname).removeClass('selected');
				$(controller).addClass('selected');
				$(controller).removeClass('unselected');
				$('.tabbed.'+groupname).hide();
				$(element).show();
			})
		})
	}

	
function hank(){
	/***************************************
	* This creates a comment box. 
	* ARGUMENT
	* DATA : OBJECT:
	* 	subjectValue : string
	* 	contentValue : string
	* 	aboveKeyValue : string
	* 	isUser : boolean
	* 	selfKeyValue : string
	* 	subscribeChecked : boolean
	* 	submitValue : string
	****************************************/
	this.createCommentBox = function(data,subscribeData){

		//Generate Elements
		var exit = document.createElement('span')
		var Xit = document.createTextNode('x')
		exit.appendChild(Xit)
		exit.className='exit'
		var form = document.createElement('form')
		form.className = 'postcomment'
		form.setAttribute('action','comment/')
		form.setAttribute('method','post')
		var subjectText = document.createTextNode('Subject: ')
		var subject = document.createElement('input')
		subject.type = 'text'
		subject.size = 80
		subject.name = 'subject'
		subject.value = data['subjectValue']
		var content = document.createElement('textarea')
		content.setAttribute('name','content')
		content.setAttribute('class','tinymce')
		content.setAttribute('rows','5')
		content.setAttribute('cols','67')
		if(data['contentValue']!= undefined){
			var contentText = document.createTextNode(data['contentValue'])
			content.appendChild(contentText)
			}	
		if(data['aboveKeyValue'] != undefined){
			var aboveKey = document.createElement('input')
			aboveKey.setAttribute('type','hidden')
			aboveKey.setAttribute('name','aboveKey')
			aboveKey.setAttribute('value',data['aboveKeyValue'])
		}

		
		if(data['selfKeyValue'] != undefined){
			var selfKey = document.createElement('input')
			selfKey.setAttribute('name','selfKey')
			selfKey.setAttribute('type','hidden')
			selfKey.setAttribute('value',data['selfKeyValue'])
			var deleteButton = document.createElement('input')
			deleteButton.type = 'button'
			deleteButton.className = "deleteComment"
			deleteButton.value = 'Delete'
		}
		var submit = document.createElement('input')
		submit.setAttribute('type','submit')
		submit.setAttribute('value',data['submitValue'])

		//Combine Elements
		form.appendChild(exit)
		form.appendChild(subjectText)
		form.appendChild(subject)
		form.appendChild(document.createElement("br"))
		form.appendChild(content)
		form.appendChild(document.createElement("br"))
		if(data['aboveKeyValue'] != undefined){
			form.appendChild(aboveKey)
		}
		form.appendChild(submit)
		if(data['selfKeyValue'] != undefined){
			form.appendChild(selfKey)	
			form.appendChild(document.createElement("br"))
			form.appendChild(deleteButton)
		}

		//Return
		return form				
	}
	
		
	this.tabular = function(){
			$('div.tabs').each(function(){
				var newList = document.createElement('ul')
				var mainFlag = $(this).metadata().main
				newList.className='tabs'
				//construct list as skeleton for tabs
				if(mainFlag == 'true'){
				/*The key differences between main tabs and body tabs are that 
				 *the main tab div is separated from the divs it controls by the
				 *body content div, so selector chains tend to need an extra 
				 * 'children()' to get to their target, and the two need to be 
				 * wrapped in different div classes for styling.
				 * */
					$(this).children().children('div.tab').each(function(){
						// .notab allows for titles and other elements that serve when tabs
						// can't be generated.
						$(".notab",this).hide()
						
						var data = $(this).metadata()
						var newLi = document.createElement('li')
						if(data.initial=='true'){
							$(newLi).addClass('selected tab')
						}
						else{
							$(newLi).addClass('unselected tab')
							//hide unselected tabs
							$(this).hide()
						}
						newLi.appendChild(document.createTextNode(data.name))
						newList.appendChild(newLi)
					})
					//insert tab structure
					var result = $('<div class="maintabs"></div>').append(newList)
					$(this).prepend(result)
					//set click action
					$(this).children('.maintabs').children('ul.tabs').children('li.tab').each(function(index){
						$(this).click(function(){
							if(!$(this).hasClass('selected')){
								$(this).toggleClass('selected unselected').siblings('li.tab.selected').toggleClass('selected unselected')
								$(this).closest('div.tabs').children().children('div.tab:eq('+index+'),div.tab:visible').toggle()
							}
						})
					})					
				}
				else{
					$(this).children('div.tab').each(function(){
						var data = $(this).metadata()
						var newLi = document.createElement('li')
						if(data.initial=='true'){
							$(newLi).addClass('selected tab')
						}
						else{
							$(newLi).addClass('unselected tab')
							//hide unselected tabs
							$(this).hide()
						}
						newLi.appendChild(document.createTextNode(data.name))
						newList.appendChild(newLi)
					})
					//insert tab structure
					var result = $('<div class="bodytabs"></div>').append(newList)
					$(this).prepend(result)	
					//set click action
					$(this).children('div.bodytabs').children('ul.tabs').children('li.tab').each(function(index){
						$(this).click(function(){
							if(!$(this).hasClass('selected')){
								$(this).toggleClass('selected unselected').siblings('li.tab.selected').toggleClass('selected unselected')
								$(this).closest('div.tabs').children('div.tab:eq('+index+'),div.tab:visible').toggle()
							}
						})
					})						
				}
				
						
			})
			var isIE = navigator.appName === 'Microsoft Internet Explorer';
			if(true){//!isIE
				$('.tab').corner('top')
			}
		}
	this.streamDoc = function(){
		$('.streamDocument').each(function(){
			$(this).addClass('clickable')
			var url = $('.title a',this).attr('href')
			title = $('.title a',this).html()
			$('.title a',this).replaceWith(title)
			$(this).click(function(){				
				window.location = url
			})
		})
	}
	
	this.streamComment = function(){
		$('.stream_item .comment').each(function(){
			$(this).addClass('clickable').click(function(){
				url = $('.header a',this).attr('href')
				window.location = url
			})
		})
	}
	
	this.prepareScriptVersion = function(){
		$('.scriptless').remove()
		$('.scriptOnly').show()
	}
	
}

$(document).ready(function(){
	myHank = new hank
	myHank.tabular()
	myHank.streamDoc()
	myHank.streamComment()
	myHank.prepareScriptVersion()


})

/* ROUNDIFICATION */

$(document).ready(function(){
	var isIE = navigator.appName === 'Microsoft Internet Explorer';
	if(true){//isIE
		$('div.stream_item').corner()
		$('div.pagetop').corner('40px')
		$('div.bodycontent').corner('40px')
		$('.round').corner('30px')
		$('.aButton, .interface').corner('40px')
		$('.roundtop').corner('40px top')
		$('.tagList').corner('40px')
	}
})

/////////////////////////////////////////////////////////////////
/*template should contain a string with unique replacibles
  and a context which is an array of items to be replaced and 
  their replacements. The replacibles should be surrounded with %s
 */
function template(string, context)
	{
		for(var i=0;i<context.length;i++)
		{
			var re = new RegExp('%'+context[i][0]+'%','g')
			string = string.replace(re,context[i][1])
		} 
		return string;
	} 
	
addLoadEvent( function(){
if (document.getElementsByClassName == undefined) {
	document.getElementsByClassName = function(className)
	{
		var hasClassName = new RegExp("(?:^|\\s)" + className + "(?:$|\\s)");
		var allElements = document.getElementsByTagName("*");
		var results = [];

		var element;
		for (var i = 0; (element = allElements[i]) != null; i++) {
			var elementClass = element.className;
			if (elementClass && elementClass.indexOf(className) != -1 && hasClassName.test(elementClass))
				results.push(element);
		}
		return results;
	}
}
})

addLoadEvent(function(){var myHank = new hank})

function addLoadEvent(func) {
  var oldonload = window.onload;
  if (typeof window.onload != 'function') {
    window.onload = func;
  } else {
    window.onload = function() {
      if (oldonload) {
        oldonload();
      }
      func();
    }
  }
}