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
    </head>
    <html>
    <body>

        <h1><a href="http://essayhost.appspot.com/">EssayHost.com</a></h1>
        <table style="border:solid 5px #ddd;background:#eee;padding:5px;">


            ${documents}
            

            
            ${comments}


                        
            ${streamMessages} 
            
        </table>   

    </body>
    </html>
    ''')

def prepareTextMailing(mailing):
    pass
def prepareHTMLMailing(mailing):
    
    tempDocuments = '''
            <tr>
            <td>
                <h2>New Documents</h2>
            </td>
            </tr>    
    '''
    for documentEvent in mailing['documents']:
        tempDocuments = tempDocuments + templateDocumentHTML(documentEvent) 
        
    tempComments = '''
            <tr>
            <td>
                <h2>New Comments</h2>
            </td>
            </tr>
    '''
    for commentEvent in mailing['comments']:
        tempComments = tempComments + templateCommentHTML(commentEvent)
        
    tempStreamMessages = '''
            <tr>
            <td>
                <h2>Recent Events</h2>
            </td>
            </tr>
    '''
    for message in mailing['messages']:
        tempStreamMessages =tempStreamMessages+'<tr><td>'+message.content+'</td></tr>'
    
    finalMessage = main.substitute(
                                   documents = tempDocuments,
                                   comments= tempComments,
                                   streamMessages= tempStreamMessages,                                   
                                   )
    logging.info('email message = '+finalMessage)
    return finalMessage

def templateDocumentHTML(documentEvent):
    email_document = Template(u"""
    ${reasons}
    <tr><td>
    <table style="border:solid 1px #bbb;background:#fff;width:600px;padding:5px;">
        <tr>
            <td style="font-weight:bold;font-size:20px;font-family:serif;font-variant:small-caps;">
                ${title}
            </td>
        </tr>
        <tr>
            <td style="font-size:10px;"> 
                ${date}- by <span style="font-variant:small-caps;">${author}</span>
            </td>
        </tr>
        <tr>
            <td style="border-top:solid 2px;margin-top:5px;padding:5px;">
                ${description}
            </td>
        </tr>
    </table>
    </td></tr>
    """)
      
    return email_document.substitute(
                                     reasons = templateReasonsHTML(documentEvent.reasons),
                                     title = documentEvent.object.title,
                                     date=documentEvent.object.date.date(),
                                     author=documentEvent.object.author.username,
                                     description = documentEvent.object.get_description()
                                     )    
    
def templateCommentHTML(commentEvent):
    email_comment = Template(u"""
    ${reasons}
    <tr><td>
    <table style="border:solid 1px #bbb;background:#fff;width:600px;padding:5px;">
        <tr>
            <td style="font-weight:bold;">
                Subject: ${subject}
            </td>
        </tr>
        <tr>
            <td style="font-size:10px;color:#888;"> 
                ${date} ${authorName} wrote:
            </td>
        </tr>
        <tr>
            <td style="border-top:solid 2px;padding:5px;">
                ${body}
            </td>
        </tr>
    </table>
    <td></tr>

    """)
    
    return email_comment.substitute(
                                           reasons = templateReasonsHTML(commentEvent.reasons),
                                           subject=commentEvent.object.subject,
                                           date=commentEvent.object.date.ctime(), 
                                           authorName = commentEvent.object.getAuthorName(),
                                           body = commentEvent.object.get_stripped(300)                                          
                                           )

      
    
def templateReasonsHTML(reasonsList):
    email_reason = Template(u"""
    <tr>
        <td>
            ${thisReason}
        </td>
    </tr>
    """)  
    tempReasons = ''
    for reason in reasonsList:
        tempReasons = tempReasons + email_reason.substitute(thisReason = reason)
    return tempReasons

    


