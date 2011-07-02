


// The basic tag button is an anchor linking to a corresponding tag page.
// All it needs to know to do its job is its name.

/********************************************************
 * Tab_button creates a button that will occupy the top
 * spaces of the document browser.
 *******************************************************/



/********************************************************
 * Tab_button creates a button that will occupy the top
 * spaces of the document browser.
 *******************************************************/


function Tag_button(name) {

	var resultsContainer = document.createElement('button')
			
	state = ""
	this.name = name
	resultsContainer.innerHTML = this.name
	//resultsContainer.setAttribute('href','/tag/'+this.name+'/')
	resultsContainer.setAttribute('class','tag_button '+name+'_button')
		
	this.display = function(location_id) {
		holder = document.getElementById(location_id)
		holder.appendChild(resultsContainer)	
		this.action	
	}
		
	action = function(){
		$('.'+name+'_button').click(function() {
  			alert('Handler for .click() called.');
		});
	}
}

	
function test_init(name,place) {
	var test_tag = new Tag_button(name)
	test_tag.display(place)
}

function hello(message) {
	var container = document.getElementById("test_container");
	container.innerHTML = message;
}
	
function intermediary() {
	place = "test_container"
	test_init(name, place)
}
	
window.onload = intermediary;



//window.load = test_init('test_tag','test_container');