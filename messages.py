# coding: utf-8 
from string import Template
import logging

domainstring='http://essayhost.appspot.com/'

##################################################
#         STYLE SHEET
#
    
main =Template(u'''
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />

     <style type="text/css">
     /* Client-specific Styles */
     #outlook a{padding:0;} /* Force Outlook to provide a "view in browser" button. */
     body{width:100% !important;} /* Force Hotmail to display emails at full width */
     body{-webkit-text-size-adjust:none;} /* Prevent Webkit platforms from changing default text sizes. */
     
     /* Reset Styles */
     body{margin:0; padding:0;}
     img{border:none; font-size:14px; font-weight:bold; height:auto; line-height:100%; outline:none; text-decoration:none; text-transform:capitalize;}
     #backgroundTable{height:100% !important; margin:0; padding:0; width:100% !important;}
    
     /* Template Styles */
    
    body{
    max-width:600px;
    }
    
     /***** MAIN *****/
     
    #frame{
    border:solid 20px;
    border-color: #d1d1d1;
    border-right:100px;
    border-bottom:100px;
    }
    
    #mainhead{
    font-family: 'palatino linotype' ‘Book Antiqua’, Palatino, serif;
    color: #eee;
    background: #242e2f
    max-width: 30%;
   } 

    /***** DOCUMENTS *****/
   
    .document{
    color:#000;
    font-family: "Times New Roman",Times,serif;
    border:solid 1px;
    border-color: #aaa;
    overflow:hidden;
    padding:5px;
    max-height:125px;
    margin-bottom:5px;
    }

   
    .description{
    font-size:18px;
    }
   
    .info{
    font-size:10px;
    }
   
    .title_link{
    color:#111;
    }
   
    .title{
    font-size:24px;
    font-variant: small-caps;
    }

    /**** COMMENTS ******/
    
    .comment{
    font-family: 'palatino linotype' ‘Book Antiqua’, Palatino, serif;
    color:#000;
    border:solid 1px;
    border-color: #aaa;
    margin-bottom:5px;
    }
 
    .subject{
    color: #fff;
    background: #242e2f;
    }
    
    .info_comment{
    background: #ddd;
    }
    
    .comment_content{
    background-color:#eee;
    }
   
    </style>
    
    </head>
    <html>
    <body>
    <div id="frame">
        <h1 id="mainhead">Essay.com</h1>
        ${content}
    </div>
    </body>
    </html>
    ''')
    
########################################################
#               EMAIL DOCUMENT INFO
#

def email_document(document):
    email_document = Template(u"""
    At ${date} ${author} published:
    Title: ${title} Link:${url}
    Description: ${description}
    """)
    return email_document.substitute(
                                     date=str(document.date),
                                     author=document.author.username,
                                     url=document.get_url(),
                                     title=document.title,
                                     description = document.get_description()
                                     )

def email_document_html(document):
    email_document = Template(u"""
    <div class="document">
    <span class="info">At ${date} ${author} published:</span><br/><hr/>
    <a href="${domain}/${author}/document/${filename}/" target="_blank"><h1 class="title">${title}</h1></a>
    <p class="description">${description}</p>
    </div>
    """)
    htmlcontent =  email_document.substitute(
                                     date=str(document.date),
                                     author=document.author.username,
                                     url=document.get_url(),
                                     title=document.title,
                                     description = document.get_description()
                                     )
    return main.substitute(content=htmlcontent)
   
##########################################################
#             EMAIL COMMENT INFO
#  
  
def email_comment(comment):
    email_comment = Template(u"""
    ${author} commented on ${pageobject}: Link:${urllink}
    
    Subject: ${subject} 
    At ${date} ${author} wrote: 
    
    Comment: ${body}
    """)
    
    url = comment.get_page_object().get_url()
    
    try: 
        comment.get_page_object().subtitle
        regarding = comment.get_page_object().title
    except: 
        regarding = comment.get_page_object().username
    
    try:
        authorurlfetch=comment.author.get_url()
        authorfetch=comment.author.username
    except:
        authorurlfetch = ''
        authorfetch='anonymous'
        
    if len(comment.stripped_content)>300:
        content = comment.stripped_content[:300]+'... follow link to read the rest of '+comment.author+'\'s comment.'
    else:
        content = comment.stripped_content
        

    
    return email_comment.substitute(
                                     date=str(comment.date),
                                     author=authorfetch,
                                     urllink=url,
                                     subject=comment.subject,
                                     pageobject=regarding,
                                     body = content
                                     )

    

def email_comment_html(comment):
    email_comment = Template(u"""
    <div class="comment">
    <a href="authorurl" target="_blank">${author}</a> 
    <a href="${urllink}" target="_blank">responded</a> to 
    <a href="${urllink}" target="_blank">${page}</a>
    <div class="subject">${subject}</div>
    <div class="info_comment">At ${date} ${author} wrote:</div>
    <p class="comment_content">${body}</p>
    </div>
    """)
    
    url = comment.get_page_object().get_url()
    
    try: 
        comment.get_page_object().subtitle
        regarding = comment.get_page_object().title
    except: 
        regarding = comment.get_page_object().username
        
    try:
        authorurlfetch=comment.author.get_url()
        authorfetch=comment.author.username
    except:
        authorurlfetch = ''
        authorfetch='anonymous'

    if len(comment.stripped_content)>300:
        content = comment.stripped_content[:300]+'... follow link to read the rest of '+comment.author.username+'\'s comment.'
    else:
        content = comment.stripped_content
    
    htmlcontent = email_comment.substitute(
                                     page = regarding,
                                     date=str(comment.date),
                                     author=authorfetch,
                                     authorurl=authorurlfetch,
                                     urllink=url,
                                     subject=comment.subject,
                                     body = content
                                     )
    return main.substitute(content=htmlcontent)
                                     