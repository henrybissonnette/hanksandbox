


/********************************************************
 * tag_browser organizes the creation of a button based 
 * broweser that allows users to view documents by tag.
 * The basic structure of the tag browser is three divs.
 * One for the tag path, one with further subtag divisions
 * and a third for displaying the actual documents.
 * 
 * ARGUMENT: LOCATION - string - id of the
 * 	page element into which the browser should be dropped.
 * ARGUMENT: DATA - JSON object containing:
 * 	ELEMENT: focal_tag - string
 *  ELEMENT: path - array of strings
 *  ELEMENT: children - array of strings
 *  ELEMENT: documents - array of objects
 *   Element: title - string
 *   Element: description - string
 *   Element: author - string
 *   Element: date - string 
 *   Element: key - string
 *   Element: filename - string
 *   Element: rating - int
 *   Element: favorites - int
 *   Element: comments - int
 *******************************************************/

function tag_browser(location, data){
	
	holder = document.getElementById(location)
	holder.innerHTML = ''
	holder.className = 'document_browser'
	
	this.display_init = function(){
		
		var path = document.createElement('div')
		path.id = location + '_path'
		path.className = 'browser_path'
		
		var children = document.createElement('div')
		children.id = location+'_children'
		children.className = 'browser_children'
		
		var documents = document.createElement('div')
		documents.id = location + '_documents'
		documents.className = 'browser_documents'
				
		holder.appendChild(path)
		holder.appendChild(children)
		holder.appendChild(documents) 
		
		this.display_path()
		this.display_children()
		this.display_documents()
		$('.stream_item').corner()
	}

	this.display_path = function(){
		if(data['path']){
			/*var root_tag = new tag_button('Root',location,'path')
			root_tag.display(location+'_path')*/
			
			for (var i=data['path'].length-1;i>=0;i--){
				var new_tag = new tag_button(data['path'][i],location,'path')
				new_tag.display(location+'_path')
				}
				
			var bar = document.createTextNode('|')
			document.getElementById(location+'_path').appendChild(bar)
			
			var new_tag = new tag_button(data['focal_tag'],location,'focal')
			new_tag.display(location+'_path')
		}

	}
	
	this.display_children = function(){
		for (i=0;i<data['children'].length;i++){
			var new_tag = new tag_button(data['children'][i],location,'child')
			new_tag.display(location+'_children')
			}
	}
	
	this.display_documents = function(){
		for (i=0;i<data['documents'].length;i++){
			var new_doc = new streamDoc(data['documents'][i])
			new_doc.display_init(location+'_documents')
		}
	}
	
	this.newInstance = function(){
		this.ajaxify(location,"Root")
	}
	
	this.ajaxify = function(location,tag){
		$(document).ready(function(){		
					$.ajax({
						type: "POST",
						url: "tag_browser/",
						data: "tag=" + tag,
						success: function(data){
							browserInfo = eval('('+data+')')
							browser = new tag_browser(location,browserInfo)
							browser.display_init()
						}
		
					})
			})
	}
}

/********************************************************
 * tag_button creates a button that will occupy the top
 * spaces of the document browser. The button needs three
 * arguments:
 * ARGUMENT: name - string - must be valid tag name
 * ARGUMENT: browser_div - string - id of location to be 
 * 	loaded on click
 * ARGUMENT: type - string - path, focal, or child
 *******************************************************/

function tag_button(name,browser_div, type) {

	var resultsContainer = document.createElement('span'),
		holder;
			
	state = ""
	this.name = name
	resultsContainer.innerHTML = this.name
	resultsContainer.className = 'tag_button '+type+'_button'
	resultsContainer.id = name+'_button'
		
	this.display = function(location_id) {
		holder = document.getElementById(location_id)
		holder.appendChild(resultsContainer)	
		resultsContainer.onclick = ajaxify
	}
	
	
	ajaxify = function(){
		$(document).ready(function(){		
					$.ajax({
						type: "POST",
						url: "tag_browser/",
						data: "tag=" + name,
						success: function(data){
							browserInfo = eval('('+data+')')
							browser = new tag_browser(browser_div,browserInfo)
							browser.display_init()
						}
		
					})
			})
	}
	
}

/********************************************************
 * streamDoc builds a summary document display out of a doc
 * data object.
 * ARGUMENT: DOCUMENT
 *  ELEMENT: title - string
 *  ELEMENT: description - string
 *  ELEMENT: date - string
 *  ELEMENT: author - string
 *  ELEMENT: key - string
 *  ELEMENT: filename - string
 *  ELEMENT: rating - int
 *  ELEMENT: favorites - int
 *  ELEMENT: comments - int
 *******************************************************/

function streamDoc(doc){
	this.display_init = function(location){
		
		holder = document.getElementById(location)
		
		var container = document.createElement('div')
		container.id = location + '_streamDoc_'+doc['key']
		container.className = 'browser_streamDoc stream_item clickable'
		container.onclick = direct
		
		var statlist = document.createElement('ul')
		var ratingLi = document.createElement('li')
		if(doc['rating']>=0){
			ratingLi.innerHTML = '+'+doc['rating']
		}
		else{
			ratingLi.innerHTML = doc['rating']
		}	
		statlist.appendChild(ratingLi)
			
		if(doc['favorites']!=0){
			var favLi = document.createElement('li')
			favLi.innerHTML='|'
			var imgStar = document.createElement('img')
			imgStar.src = "/static/images/star_48px.png"
			imgStar.height = "16"
			imgStar.width = "16"
			var favs = document.createTextNode(doc['favorites'])
			favLi.appendChild(imgStar)
			favLi.appendChild(favs)
			statlist.appendChild(favLi)
		}
		
		var commentsLi = document.createElement('li')	
		commentsLi.innerHTML ='|'+'comments: '+doc['comments']
		statlist.appendChild(commentsLi)	

		var title = document.createElement('div')
		title.className = 'title'
		title.innerHTML = doc['title']
		
		var header = document.createElement('div')
		header.className='header'
		header.innerHTML = doc['date']+'- <a href="/user/'+doc['author']+'/" class="username">'+doc['author']+'</a> '

		var content = document.createElement('div')
		content.className = 'stream_description'
		content.innerHTML = doc['description']
		
		container.appendChild(statlist)
		container.appendChild(title)
		container.appendChild(header)
		container.appendChild(content)
		holder.appendChild(container)
		
		$(document).ready(function(){
			$('#{{doc.filename}}').addClass('clickable')
			$('#{{doc.filename}}').click(function(){
			window.location.href = "/{{doc.author.username}}/document/{{doc.filename}}/";
			})
		})
		
	}
	
	direct = function(){
		window.location.href = "/"+doc['author']+"/document/"+doc['filename']+"/"
	}
}

/********************************************************
 * MAIN 
 *******************************************************/
	
	
function intermediary() {
	
	myBrowser = new tag_browser('tag_browser')
	myBrowser.newInstance()
	
}
	
window.onload = intermediary;



//window.load = test_init('test_tag','test_container');