# coding: utf-8 
from string import Template
import logging

domainstring='http://essayhost.appspot.com/'

##################################################
##            HTML Email                        ##
##################################################
    
mainHTML =Template(u'''
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

def prepareHTMLMailing(mailing):
    
    tempDocuments = ''
    tempComments = ''
    tempStreamMessages = ''
    
    if mailing['documents']:
        tempDocuments = '''
                <tr>
                <td>
                    <h2>New Documents</h2>
                </td>
                </tr>    
        '''
        for documentEvent in mailing['documents']:
            tempDocuments = tempDocuments + templateDocumentHTML(documentEvent) 
        
    if mailing['comments']:
        tempComments = '''
                <tr>
                <td>
                    <h2>New Comments</h2>
                </td>
                </tr>
        '''
        for commentEvent in mailing['comments']:
            tempComments = tempComments + templateCommentHTML(commentEvent)      
        
    if mailing['messages']:
        tempStreamMessages = '''
                <tr>
                <td>
                    <h2>Recent Events</h2>
                </td>
                </tr>
        '''
        for message in mailing['messages']:
            tempStreamMessages =tempStreamMessages+'<tr><td>'+message.content+'</td></tr>'
    
    finalMessage = mainHTML.substitute(
                                   documents = tempDocuments,
                                   comments= tempComments,
                                   streamMessages= tempStreamMessages,                                   
                                   )
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

##################################################
##            Text Email                        ##
##################################################
    
mainText =Template(u'''
bliterati (www.bliterati.com)

${documents}\r\n
             
${comments}\r\n

${streamMessages}\r\n
            

''')

def prepareTextMailing(mailing):
    
    tempDocuments = ''
    tempComments = ''
    tempStreamMessages = ''
    
    if mailing['documents']:
        tempDocuments = 'NEW DOCUMENTS \r\n\r\n'
        
        for documentEvent in mailing['documents']:
            tempDocuments = tempDocuments + templateDocumentHTML(documentEvent)   
    
    if mailing['comments']:        
        tempComments = 'NEW COMMENT\r\n\r\n'
        for commentEvent in mailing['comments']:
            tempComments = tempComments + templateCommentHTML(commentEvent)
    
    if mailing['messages']:   
        tempStreamMessages = 'RECENT EVENTS\r\n\r\n'
        for message in mailing['messages']:
            tempStreamMessages =tempStreamMessages+message.content+'\r\n'
    
    finalMessage = main.substitute(
                                   documents = tempDocuments,
                                   comments= tempComments,
                                   streamMessages= tempStreamMessages,                                   
                                   )
    return finalMessage

def templateDocumentHTML(documentEvent):
    email_document = Template(u"""
    ${reasons}
    ${title}\r\n
    ${date}- by ${author}\r\n
    ${description}\r\n\r\n
    """)
      
    return email_document.substitute(
                                     reasons = templateReasonsHTML(documentEvent.plainTextReasons),
                                     title = documentEvent.object.title,
                                     date=documentEvent.object.date.date(),
                                     author=documentEvent.object.author.username,
                                     description = documentEvent.object.get_description()
                                     )    
    
def templateCommentHTML(commentEvent):
    email_comment = Template(u"""
    ${reasons}
    Subject: ${subject}\r\n
    ${date} ${authorName} wrote:\r\n
    ${body}\r\n\r\n
    """)
    
    return email_comment.substitute(
                                           reasons = templateReasonsHTML(commentEvent.plainTextReasons),
                                           subject=commentEvent.object.subject,
                                           date=commentEvent.object.date.ctime(), 
                                           authorName = commentEvent.object.getAuthorName(),
                                           body = commentEvent.object.get_stripped(300)                                          
                                           )

      
    
def templateReasonsHTML(reasonsList):
    email_reason = Template(u"${thisReason}\r\n")  
    tempReasons = ''
    for reason in reasonsList:
        tempReasons = tempReasons + email_reason.substitute(thisReason = reason)
    return tempReasons

