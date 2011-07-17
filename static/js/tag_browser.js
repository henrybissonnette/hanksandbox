


/********************************************************
 * tag_browser organizes the creation of a button based 
 * broweser that allows users to view documents by tag.
 * The basic structure of the tag browser is three divs.
 * One for the tag path, one with further subtag divisions
 * and a third for displaying the actual documents.
 * 
 * ARGUMENT: LOCATION is a string with the id of the
 * page element into which the browser should be dropped.
 * 
 * ARGUMENT: DATA is a JSON object containing:
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
 *   
 *******************************************************/

test_data = {'focal_tag':'Hank','path':['grandparents','parents'],'children':['stevo','bobby','ted nugent','Meta'], 
'documents':[{'title':'test document 1','author':'hank','description':'to go where no document has gone before','date':'7/16/2011','key':'secret','filename':'first-doc'}]}

function tag_browser(location, data){
	
	holder = document.getElementById(location)
	holder.innerHTML = null
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
	}

	this.display_path = function(){
		if(data['path']){
			var root_tag = new tag_button('root',location)
			root_tag.display(location+'_path')
			for (i=0;i<data['path'].length;i++){
				var new_tag = new tag_button(data['path'][i],location)
				new_tag.className='tag_button path_button'
				new_tag.display(location+'_path')
				}
			var bar = document.createTextNode('|')
			document.getElementById(location+'_path').appendChild(bar)
			var new_tag = new tag_button(data['focal_tag'],location)
			new_tag.className='tag_button focal_button'
			new_tag.display(location+'_path')
		}

	}
	
	this.display_children = function(){
		for (i=0;i<data['children'].length;i++){
			var new_tag = new tag_button(data['children'][i],location)
			new_tag.className='tag_button child_button'
			new_tag.display(location+'_children')
			}
	}
	
	this.display_documents = function(){
		for (i=0;i<data['documents'].length;i++){
			var new_doc = new streamDoc(data['documents'][i])
			new_doc.display_init(location+'_documents')
		}
	}
	
	this.new = function(){
		ajaxify(location,"root")
	}
	
	ajaxify = function(location,tag){
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
 * spaces of the document browser.
 *******************************************************/

function tag_button(name,browser_div) {

	var resultsContainer = document.createElement('button')
			
	state = ""
	this.name = name
	resultsContainer.innerHTML = this.name
	//resultsContainer.setAttribute('href','/tag/'+this.name+'/')
	//resultsContainer.setAttribute('class','tag_button '+name+'_button')
	resultsContainer.className='tag_button '
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
 * streamDoc builds a document display out of a doc
 * data object.
 * ARGUMENT: DOCUMENT
 *  ELEMENT: title - string
 *  ELEMENT: description - string
 *  ELEMENT: date - string
 *  ELEMENT: author - string
 *  ELEMENT: key - string
 *  ELEMENT: filename - string
 *******************************************************/

function streamDoc(doc){
	this.display_init = function(location){
		
		holder = document.getElementById(location)
		
		var container = document.createElement('div')
		container.id = location + '_streamDoc_'+doc['key']
		container.className = 'browser_streamDoc stream_item clickable'
		container.onclick = direct
		

		var title = document.createElement('div')
		title.className = 'stream_title'
		title.innerHTML = doc['title']
		
		var header = document.createElement('div')
		header.className='stream_header'
		header.innerHTML = doc['date']+'- <a href="/user/'+doc['author']+'/">'+doc['author']+'</a> '
		

		var content = document.createElement('div')
		content.className = 'stream_description'
		content.innerHTML = doc['description']
		
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
	
function test_init(name,place) {
	var test_tag = new tag_button(name)
	test_tag.display(place)
}

function hello(message) {
	var container = document.getElementById("test_container");
	container.innerHTML = message;
}
	
function intermediary() {
	
	myBrowser = new tag_browser('tag_browser',test_data)
	myBrowser.new()
	
}
	
window.onload = intermediary;



//window.load = test_init('test_tag','test_container');