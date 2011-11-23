$(document).ready(function(){
	
	loader = new Image(10, 10); 
	loader.src = '/static/images/loader.gif';
	
	var is_in_use = false
	var forbidden = "`~!@#$%^&*()+={}[]\\|:;\"\'<>,. ";
		
	function validate_username()
		{
			var x=document.getElementById("username").value;
			if (x==null || x=="")
			  {
				  alert("Username is required.");
				  return false;
			  }
			for(i=0;i < forbidden.length;i++)
				{
					if (x.indexOf(forbidden.charAt(i)) != -1)
					{
						alert("Usernames may only contain A-z, 1-9, _ , and -.");
						return false;
					}
				}

			if (is_in_use)
				{
					alert("This username already exists, you must choose a unique username.");
					return false;
				}
		}


		
	$('form#entry').submit(function(){
		return validate_username()
		})
	
	$('#username').bind('keyup paste cut',function(){	
		
		var user = $('#username').val();
			
		if(user.length >= 1)
		{
			$('#status').html('<img class="loader_img" src="/static/images/loader.gif"/> Checking availability...');
				
			$.ajax({
				type: "POST",
				url: "availability/",
				data: "username=" + user,
				success: function(message){
					$('#status').ajaxComplete(function(event,request,settings){
						if(message == "1")
						{
							is_in_use = false;
							$(this).html('username available');	
						}
						else if(message =="00")
						{
							is_in_use = true;
							$(this).html('username already in use');	
						}
						else if(message =="01")
						{
							$(this).html('username may only contain A-z, 1-9, _ , and -');	
						}
						else
						{
							$(this).html('error unknown');	
						}
									
					})
				}
	
			})
		}
				
	})
			
})

