# coding: utf-8 
from google.appengine.dist import use_library
use_library('django', '1.2')

from os import path
from google.appengine.api import mail, memcache, users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from cgi import escape
from django.utils.html import strip_tags
import os, re, logging, sys,datetime,math,urllib
import messages, string, random
from BeautifulSoup import BeautifulSoup
from django.utils import simplejson as json

hank = {
        'domainstring':'http://essayhost.appspot.com/',
        'adminlist':['henrydbissonnette@gmail.com','Joseph.A.Bissonnette@gmail.com'],
        'updatingModel':None,
        }

def get_document(name, filename, title=None):

    user = get_user(name)
    try:
        if filename:
            document = Document.all().filter('author ==',user).filter('filename ==',filename)[0]
        else:
            document = Document.all().filter('author ==',user).filter('title ==',title)[0]
        #temporary fix for obsolete authornames
        document.authorname = user.username
        document.put()
        return document

    except:
        return None

def get_documents(tag_list=[], tag_not_list=[], number=1000, draft=False, type=None, specialType=None, since=None):
    """ tag_list should be a string list of tags """
        
    document_query = Document.all()
    if specialType:
        document_query.filter("type ==",specialType)
    else:
        document_query.filter("special ==",False)
    if not draft:
        document_query.filter("draft ==",False)
    if type: 
        document_query.filter("type ==",type)
    if since:
        document_query.filter("date >=",since)    
    
    for tag in tag_list:
        document_query.filter("tags ==",tag)
    for tag in tag_not_list:
        document_query.filter("tags !=",tag)
    document_query.filter("draft ==",False)
    documents = document_query.order('-date').fetch(number)
    return documents


def get_user(name=None):
    """If a name is supplied get user returns the user with that username otherwise
    it returns the current user."""
    if name:
        name = name.lower()
    if name:
        try:
            user = User.all().filter('username ==', name).fetch(1)[0]
        except: 
            return None
    else:
        try:
            user = User.all().filter('google ==', users.get_current_user()).fetch(1)[0]
        except:
           return None
    if user == None:
        return None
    #this is one time use for correcting prelowercase usernames
    if user.username:
        user.username = user.username.lower()
    
    return user

def cleaner(value, deletechars = ' `~!@#$%^&*()+={[}]|\"\':;?/>.<,'):
    value = strip_tags(value)
    for c in deletechars:
        value = value.replace(c,'')
    return value;

def is_document(object):
    try:
        test = object.filename
        test = object.subtitle
        return True
    except:
        return False

def remove_duplicates(seq, idfun=None): 
    # order preserving
    if idfun is None:
       #why use this instead of plain old equality?
       def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker in seen: 
            continue
        seen[marker] = 1
        result.append(item)
    return result
    
class CommentaryObj:
    """
    Intended to replace the awkward code of the commentary object. Should be
    an object that is perfectly JSON compatible and gives all the info necessary
    to perform arbitrarily complex comment filtering. 
    STRUCTURE:
    Comment - dictionary
        Children - list of child CommentaryObjs
        
    """
    
    
class Commentary:
    """commentary needs to be supplied with a user and also, optionally, 
    a document. In the event that you supply a document commentary 
    believes you are creating the comment tree for that document. Otherwise
    it will assume that you want the comment tree for the user's page.
    
    In either case it will generate the callable comment_data for inclusion
    in context, though that approach is technically obsolete with the creation 
    of commentary objects."""
    
    def comment_tree_expand(self, comment, depth = 0):
    
        # temporary stripped content maker
        if not comment.stripped_content:
            comment.stripped_content = strip_tags(comment.content)
            comment.put()
        # end temporary
        tree = [(comment,depth)]
            
        if comment.replies:
            for sub_comment in comment.replies:
                
                tree.extend(self.comment_tree_expand(sub_comment, depth+1))
        
        return tree
    
    def prepare_reply_tree(self, comments):
        """Returns a two element tuple. return_tree[0] contains
        and ordered list of all of the comments and subcomments,
        while return_tree[1] contains an ordered list of all of 
        their depths. """
        
        tree = []
        
        for comment in comments:
            tree.extend(self.comment_tree_expand(comment))
        return_tree = ([x[0] for x in tree],[x[-1] for x in tree])
    
        return return_tree
    
    def delta_builder(self, depth_list):
        """Delta builder takes a list of depths from prepare_reply_tree
        and differences them. These differences are then turned into an
        array of lists including (-1,1). Each top level element in this 
        array represents a comment. Each -1 represents a decrease in depth
        each +1 indicates an increase in depth. Empty lists represent no 
        change in depth. This allows the template system to manage indentation 
        when building the comment tree in page."""
        delta_return = []
    
        depth_list.insert(0,0)     
        delta = [a-b for a,b in zip(depth_list[1:], depth_list[:-1])]
        for i in range(len(delta)):
            delta_sub = []
            temp = delta[i]
            while temp !=0:
                if temp > 0:
                    delta_sub.append(1)
                    temp = temp - 1
                else:
                    delta_sub.append(-1)
                    temp = temp + 1
            delta_return.append(delta_sub)
        return delta_return
    
    def __init__(self, username, document_filename=None,document_title=None):
        
        if document_filename:
            document = get_document(username, document_filename)
            draftCheck = document.draft
            self.comments = document.comments.order('-date').filter('draft ==',draftCheck)
        else:      
            self.comments = get_user(username).mypagecomments.order('-date')
            
        self.comment_tree = self.prepare_reply_tree(self.comments)
        self.delta =  self.delta_builder(self.comment_tree[1])  
        self.sum_delta = [1] * sum([item for sublist in self.delta for item in sublist])
        self.keys = [str(comment.key()) for comment in self.comment_tree[0]]   
        self.comment_data = zip(self.comment_tree[0], self.keys, self.delta)
    
class User(db.Model):
    """
    USER accesses the collections:
    
    works (created documents)
    mycomments (created comments)
    bugs (submitted bug reports)
    ratings (submitted votes)
    """
    age = db.IntegerProperty()
    circle = db.StringListProperty(default=[])
    circlepermissions = db.StringListProperty(default=[])
    date = db.DateTimeProperty(auto_now_add=True)
    displayname = db.StringProperty()
    email_log = db.ListProperty(db.Key,default=[])
    favorites = db.ListProperty(db.Key,default=[])
    fistname = db.StringProperty(default='')
    lastname = db.StringProperty(default='')
    google = db.UserProperty()
    invitations = db.StringListProperty(default=[])
    invitees = db.StringListProperty(default=[])
    reputation = db.IntegerProperty(default=1)
    
    # people who subscribe to me in some way
    subscribers = db.StringListProperty(default=[])
    # people who subscribe to my documents by email
    subscribers_document=db.StringListProperty(default=[])
    # people who subscribe to my comments by email
    subscribers_comment=db.StringListProperty(default=[])
    # people I subscribe to
    subscriptions_user = db.StringListProperty(default=[])
    # people whose comments go in my stream
    subscriptions_comment = db.StringListProperty(default=[])
    # people whose documents go in my stream
    subscriptions_document = db.StringListProperty(default=[])
    # tags I subscribe to
    subscriptions_tag = db.StringListProperty(default=[])

    minimizeThreshold = db.IntegerProperty(default=3)
    namePreference = db.StringProperty(default='username')
    object_type = db.StringProperty(default = 'User')
    username = db.StringProperty()
    
    def is_admin(self):
        if self.google.email() in hank['adminlist']:
            return True
        else:
            return False

    def get_age(self):
        age = datetime.datetime.now()-self.date
        return age.days
    
    def get_commentary(self):
        commentary = Commentary(self.username)
        return commentary
    
    def acceptInvitation(self, username):
        self.circlepermissions.append(username)
        self.invitations.remove(username)
        inviter = get_user(username)
        inviter.invitees.remove(self.username)
        inviter.circle.append(self.username)
        self.put()
        inviter.put()
        # stream message
        message = StreamMessage()
        message.recipient = inviter
        message.content = self.get_url(html=True)+' has accepted your circle invitation.'
        message.put()
    
    def add_favorite(self, document):
        if not document.key in self.favorites:
            self.favorites.append(document.key())
        if not self.username in document.favorites:
            document.favorites.append(self.username)
        document.put()
        self.put()
    
    def addModPoint(self):
        logging.info('selected user = '+self.username)
        newPoint = ModPoint()
        newPoint.user = self
        newPoint.put()
        
    def declineInvitation(self, username):
        self.invitations.remove(username)
        inviter = get_user(username)
        inviter.invitees.remove(self.username)
        self.put()
        inviter.put()
        # steam message
        message = StreamMessage()
        message.recipient = inviter
        message.content = self.get_url(html=True)+' has declined your circle invitation.'
        message.put()
        
    def fetch_favorites(self):
        favorites = []
        for key in self.favorites:
            favorites.append(Document.get(key))
        return favorites
            
    def get_url(self, includeDomain = False, html = False):
        if includeDomain:
            return hank['domainstring']+'user/'+self.username+'/'
        elif html:
            return '<a href="/user/'+self.username+'/" class="username">'+self.username+'</a>'
        else:
            return '/user/'+self.username+'/'
    
    def drafts(self):
        self.works.filter('draft ==', True)
        
    def invite(self, username):
        if not username in self.invitees:
            self.invitees.append(username)
            invited = get_user(username)
            invited.invitations.append(self.username)
            self.put()
            invited.put()     
            # stream message
            message = StreamMessage()
            message.recipient = invited
            message.content = 'You\'ve been invited to join '+self.get_url(html=True)+'\'s Writer\'s Circle'
            message.put()
            
    def leaveCircle(self, username):
        self.circlepermissions.remove(username)
        other = get_user(username)
        other.circle.remove(self.username)
        self.put()
        other.put()
        # stream message
        message = StreamMessage()
        message.recipient = other
        message.content = self.get_url(html=True)+' has left your Writer\'s Circle'
        message.put()
        
    def modPointCount(self):
        return len(self.modPoints.fetch(1000))
        
    def publications(self):
        self.works.filter('draft ==', False)
        
    def fetch_stream(self,number=100):

        documents=[]
        horizon = datetime.datetime.now()-datetime.timedelta(weeks=1)
        
        for name in self.subscriptions_comment:
            subscribee = get_user(name)
            documents.extend(Comment.all().filter('author ==',subscribee).filter('date >=', horizon).order('-date').fetch(number))
            
        for name in self.subscriptions_document:
            subscribee = get_user(name)
            documents.extend(Document.all().filter('author ==',subscribee).filter('date >=', horizon).order('-date').fetch(number))
            
        for tag in self.subscriptions_tag:
            documents.extend(get_documents([tag],number=number))
            
        documents.extend(self.streamMessages)
            
        ordered = sorted(documents, key=lambda document: document.date, reverse=True)
        return ordered[:number]
    
    def remove(self):
        affected = []
        
        for username in self.circle:
            other = get_user(username)
            other.circlepermissions.remove(self.username)
            other.put()     
            affected.append(other)       
            
        for username in self.circlepermissions:
            other = get_user(username)
            other.circle.remove(self.username)
            other.put()
            affected.append(other)  
            
        for username in self.invitations:
            other = get_user(username)
            other.invitees.remove(self.username)
            other.put()     
            affected.append(other) 
            
        for username in self.invitees:
            other = get_user(username)
            other.invitations.remove(self.username)
            other.put()     
            affected.append(other)   
            
        for username in self.subscribers:
            other = get_user(username)
            other.set_subscription([],self.username) 
            affected.append(other)        
            
        for username in self.subscriptions_user:
            other = get_user(username)
            self.set_subscription([],username) 
            affected.append(other)      
            
        for comment in self.mycomments:
            try:
                comment.remove()
            except:
                pass
            
        for comment in self.mypagecomments:
            comment.remove(message='Your comment on '+self.username+'\'s page has been deleted because '+self.username+'\'s account has been deleted.')
            
        for document in self.works:
            document.remove()
            
        for message in self.streamMessages:
            message.remove()
            
        for rating in self.ratings:
            rating.delete()
            
        #deliver message to affected
        affected = remove_duplicates(affected)
        for user in affected:
            message = StreamMessage()
            message.recipient = user
            message.content = self.username+'\'s account has been deleted. RIP '+self.username
            message.put()
            
        self.delete()
             
    
    def removeCircle(self, username):
        """Ejects username from this user's circle"""
        self.circle.remove(username)
        other = get_user(username)
        other.circlepermissions.remove(self.username)
        self.put()
        other.put()
        # stream message
        message = StreamMessage()
        message.recipient = other
        message.content = 'You have been removed from '+self.get_url(html=True)+'\'s Writer\'s Circle'
        message.put()
    
    def set_reputation(self):
        
        #reputation=1
        #myworks = self.works.fetch(1000)
        #mycomments = self.mycomments
        #total_views = 0
            
        #for document in myworks:
        #    reputation = reputation + 4*document.rating
        #    total_views = total_views + document.views
        
        #for comment in mycomments: 
        #    reputation = reputation + comment.rating
            
        #if self.get_age() < 100:
        #    reputation = reputation*math.sqrt(self.get_age())/10
            
        #if reputation < 0:
        #    reputation = -(math.sqrt(math.fabs(reputation))/100)*97
        #else:
        #    reputation = (math.sqrt(reputation)/100)*97
            
        #prolificity = len(myworks)
        #if prolificity >= 1:
        #    reputation = reputation + 1           
        #    if prolificity >= 10:
        #        reputation = reputation + 1
        #        if total_views/prolificity <= 20:
        #            reputation = reputation - 2
        #        if prolificity >= 30:
        #            reputation = reputation + 1 
        #            if total_views/prolificity <= 30:
        #                reputation = reputation - 2
        comments = self.mycomments  
        works = self.works
        rep = 0
        for comment in comments:
            rep += comment.rating
        for work in works:
            rep += work.rating             
        self.reputation = rep  
        self.put()
        
    def set_subscription(self, subscriptions, subscribee):
        """ SUBSCRIPTIONS is a list of values (0,1) one each for email and stream 
        subscription on either comments or documents. Subscribee should be a 
        username string. """
        flag = None
        subscribee = get_user(subscribee)
        if not subscriptions:
            if self.username in subscribee.subscribers:
                    subscribee.subscribers.remove(self.username)

            if subscribee.username in self.subscriptions_user:
                    self.subscriptions_user.remove(subscribee.username)

            message = 'This user has been removed from your subscriptions.'    
        else:
            if self.username not in subscribee.subscribers:
                    subscribee.subscribers.append(self.username)
                    flag = 1

            if subscribee.username not in self.subscriptions_user:
                    self.subscriptions_user.append(subscribee.username)
                    flag = 1
               
        if flag:
            message = 'This user has been added to your subscriptions.' 
        else:
            message = 'Your settings have been saved.'
        
        if 'subscribe_publish' in subscriptions:
            if not subscribee.username in self.subscriptions_document:
                self.subscriptions_document.append(subscribee.username)
        else:
            if subscribee.username in self.subscriptions_document:
                self.subscriptions_document.remove(subscribee.username)
                
        if 'email_publish' in subscriptions:
            if not self.username in subscribee.subscribers_document:
                subscribee.subscribers_document.append(self.username)
        else:
            if self.username in subscribee.subscribers_document:
                subscribee.subscribers_document.remove(self.username)
                
        if 'subscribe_comment' in subscriptions:
            if not subscribee.username in self.subscriptions_comment:
                self.subscriptions_comment.append(subscribee.username)
        else:
            if subscribee.username in self.subscriptions_comment:
                self.subscriptions_comment.remove(subscribee.username)
        
        if 'email_comment' in subscriptions:
            if not self.username in subscribee.subscribers_comment:
                subscribee.subscribers_comment.append(self.username)
        else:
            if self.username in subscribee.subscribers_comment:
                subscribee.subscribers_comment.remove(self.username)
        
        subscribee.put()
        self.put()
        return message
    
    def subscribeTag(self, tagTitle, subscribe):
        logging.info('in subscribe tag')
        if subscribe and not tagTitle in self.subscriptions_tag:
            logging.info('subscribing')
            self.subscriptions_tag.append(tagTitle)
        if not subscribe and tagTitle in self.subscriptions_tag:
            logging.info('unsubscribing')
            self.subscriptions_tag.remove(tagTitle)
        self.put()
        
    def useModPoint(self):
        points = self.modPoints.order('date').fetch(1000)
        points[0].delete()
        
    def withdrawCircle(self, username):
        self.invitees.remove(username)
        other = get_user(username)
        other.invitations.remove(self.username)
        self.put()
        other.put()
        # stream message
        message = StreamMessage()
        message.recipient = other
        message.content = self.get_url(html=True)+'\'s Writer\'s Circle invitation has been withdrawn.'
        message.put()       
        
class Document(db.Model):
    
    author = db.ReferenceProperty(User, collection_name = 'works')
    authorname = db.StringProperty()
    content = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    _description=db.StringProperty(default = '')
    draft = db.BooleanProperty(default=True)
    favorites = db.StringListProperty(default=[])
    filename = db.StringProperty()
    leaftags = db.StringListProperty(default=[])
    object_type = db.StringProperty(default = 'Document')
    raters = db.StringListProperty()
    rating = db.IntegerProperty(default=0)
    subscribers = db.StringListProperty(default=[])
    subtitle = db.StringProperty(default='')
    tags = db.StringListProperty(default=[])
    title = db.StringProperty()
    views = db.IntegerProperty(default=0)
    viewers = db.StringListProperty(default=[])
    special = db.BooleanProperty(default=False)
    type = db.StringListProperty(default=["not_meta"])
    
    def get_commentary(self):
        commentary = Commentary(self.author.username, self.filename)
        return commentary

    def add_tag(self, tag):
        if len(self.tags) < 3:
            tags = self.tags
            tags.append(tag)
            self.add_tags(tags)
            return 'Tag added successfully.'
        else: 
            return 'A document may only have three leaf tags.'

    def add_tags(self, taglist):
        
        self.leaftags = []
        self.tags = []
        skip=False
        for tag in taglist:
            
            tagObject= Tag.get_by_key_name(tag)
            
            try:              
                Tag.get_by_key_name(tag)
                real=True
            except:
                pass
            if real:
                if tag in self.tags:
                    pass
                else:
                    for leaftag in self.leaftags:
                        if tag in Tag.get_by_key_name(leaftag).descendants:
                            self.leaftags.remove(leaftag)               
                    self.leaftags.append(tag)
                    ancestry = tagObject.ancestors
                    ancestry.append(tag)
                    self.tags.extend(ancestry)
                    self.tags = remove_duplicates(self.tags)
                    if 'Meta' in self.tags:
                        if 'meta' not in self.type:
                            try:
                                self.type.remove('not_meta')
                            except:
                                pass
                            self.type.append('meta')                    
        self.put()
    
    def get_url(self,includeDomain=False):
        if includeDomain:
            return hank['domainstring']+self.author.username+'/document/'+self.filename+'/'
        else: 
            return '/'+self.author.username+'/document/'+self.filename+'/'
    
    def get_stripped(self):
        
        stripped = strip_tags(self.content)
        #for n in range(len(stripped)):
            #if stripped[n] =='&':
                #stripped = stripped[:n]+stripped[n+5:]
        return stripped
    
    def set_description(self, words):
        words = strip_tags(words)
        words = words[:150]
        self._description=words
        
    def get_description(self):
        return self._description
    
    def get_leaftags(self):
        return [Tag.get_by_key_name(title) for title in self.leaftags]
    
    def parse(self):
        acceptableElements = ['a','blockquote','br','em','i',
                              'ol','ul','li','p','b']
        acceptableAttributes = ['href']
        counter = 0
        contentTemp = self.content  
        while True:
            counter += 1
            soup = BeautifulSoup(contentTemp)
            removed = False        
            for tag in soup.findAll(True): # find all tags
                if tag.name not in acceptableElements:
                    tag.extract() # remove the bad ones
                    removed = True
                else: # it might have bad attributes               
                    for attr in tag._getAttrMap().keys():
                        if attr not in acceptableAttributes:
                            del tag[attr]
    
            # turn it back to html
            fragment = unicode(soup)
            if removed:
                # tricks can exploit a single pass
                # we need to reparse the html until it stops changing
                contentTemp = fragment
                continue # next round           
            break   
        self.content = contentTemp
        self.put()
        
    def set_rating(self):
        votes = self.ratings 
        rating = 0
        #view_mass = 0;
        #for viewer in self.viewers:
        #    user_view = get_user(viewer)
        #    view_mass =  view_mass + (1+user_view.reputation)
        #for vote in votes:
        #    rating = rating + vote.value*(1+vote.user.reputation)
        #rating = rating/view_mass
        for vote in votes:
            rating += vote.value
        self.rating = rating
        self.put()
            
    
    def get_tags(self):
        return [Tag.get_by_key_name(title) for title in self.tags]
    
    def set_subscriber(self, subscriber, add=True):
        "Subscriber should be a username."
        if add==True and not subscriber in self.subscribers:
            self.subscribers.append(subscriber)
        if add==False and subscriber in self.subscribers:
            self.subscribers.remove(subscriber)
            
    
    def remove(self):
        
        ratings = self.ratings
        for rating in ratings:
            rating.delete()
        
        replies = self.comments
        for reply in replies:
            reply.remove(message='Your comment on '+self.title+' by '+self.authorname+' has been deleted because '+self.title+' has been deleted.')
            
        for vote in self.ratings:
            vote.delete()
        
        for username in self.favorites:
            user = get_user(username)
            user.favorites.remove(self.key())
            user.put()            
            
        self.delete()
        
    def remove_tag(self,tagName):
        current = self.leaftags
        if tagName in current:
            current.remove(tagName)
        self.add_tags(current)
        return tagName+' was removed from tags.'
        
    def set_view(self):
        if not self.draft:
            self.views += 1
            user = get_user()
            try:
                user.username
                if not user.username in self.viewers:
                    self.viewers.append(user.username)
            except:
                pass
            self.put()
            
    def get_tag_number(self):
        return len(self.tags)
    
    def votesPerView(self):
        return self.viewers/self.rating
    
    def voteRep(self):
        repSum = 0
        for vote in self.ratings:
            if vote.value > 0:
                repSum += vote.user.reputation
            if vote.value < 0:
                repSum -= vote.user.reputation
        voteRep = repSum/len(self.ratings)
        return voteRep
            
class Ticket(db.Model):
    date = db.DateTimeProperty(auto_now_add=True)
    report = db.ReferenceProperty(Document, collection_name="ticket")
    user = db.ReferenceProperty(User, collection_name="tickets")
    status = db.StringProperty(default="Open")
    message = db.StringProperty()

class Comment(db.Model):
    """It might also be more elegant to 
    manage depth with a property here."""
    author = db.ReferenceProperty(User, collection_name = 'mycomments')
    raters = db.StringListProperty()
    commentType = db.TextProperty()
    content = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    draft = db.BooleanProperty(default=False)
    above = db.SelfReferenceProperty(collection_name='replies')
    article = db.ReferenceProperty(Document,collection_name='comments')
    object_type = db.StringProperty(default = 'Comment')
    user_page = db.ReferenceProperty(User, collection_name='mypagecomments')
    rating = db.IntegerProperty(default=1)
    modifier = db.StringProperty(default=None)
    stripped_content = db.TextProperty()
    subject = db.StringProperty()
    subscribers = db.StringListProperty(default=[])
    
    def get_stripped(self):
        self.stripped_content=strip_tags(self.content)
        return self.stripped_content
    
    def get_page_object(self):
        if self.above:
            return self.above.get_page_object()
        if self.article:
            return self.article
        if self.user_page:
            return self.user_page
        
    def get_url(self):
        object = self.get_page_object()
        url = object.get_url()
        return url
    
    def parse(self):
        acceptableElements = ['a','blockquote','br','em','i',
                              'ol','ul','li','p','b']
        acceptableAttributes = ['href']
        while True:
            soup = BeautifulSoup(self.content)
            removed = False        
            for tag in soup.findAll(True): # find all tags
                if tag.name not in acceptable_elements:
                    tag.extract() # remove the bad ones
                    removed = True
                else: # it might have bad attributes
                    # a better way to get all attributes?
                    for attr in tag._getAttrMap().keys():
                        if attr not in acceptable_attributes:
                            del tag[attr]
    
            # turn it back to html
            fragment = unicode(soup)
    
            if removed:
                # we removed tags and tricky can could exploit that!
                # we need to reparse the html until it stops changing
                self.content = fragment 
                continue # next round            
            break    
        self.put()   
       
        
    def set_rating(self):
        votes = self.ratings
        rating = 1
        for vote in votes:
            if vote.value > 0:
                rating += 1
            if vote.value < 0:
                rating -= 1
        self.rating = rating
        self.put()
        #rating = 0
        #for vote in votes:
        #    rating = rating + vote        
        #if -2 < rating < 6 : 
        #    self.rating = rating
        #    self.put()
        #else: 
        #    raise Exception('comment rating would be outside -1 to 5')
    
    def remove(self, message=''):
        
        if self.author:
            if not message:
                message = 'A comment of yours was deleted because '+self.subject+' by '+self.author.username+' was deleted.'  
            else:
                streamMessage = StreamMessage()
                streamMessage.recipient = self.author
                streamMessage.content = message
                streamMessage.put()
            
        ratings = self.ratings
        for rating in ratings:
            rating.delete()
        
        children = self.replies
        for child in children:
            child.remove(message)
                    
        self.delete()
        
    def subscribe(self, user):
        if not user.username in self.subscribers:
            self.subscribers.append(user.username)
    def unsubscribe(self,user):
        if user.username in self.subscribers:
            self.subscribers.remove(user.username) 
            
class StreamMessage(db.Model):
    date = db.DateTimeProperty(auto_now_add=True)
    object_type = db.StringProperty(default='StreamMessage')
    content = db.StringProperty()
    private = db.BooleanProperty(default=True)
    recipient = db.ReferenceProperty(User, collection_name='streamMessages')
    
    def remove(self):
        self.delete()
        
class ModPoint(db.Model):
    date = db.DateTimeProperty(auto_now_add=True)
    user = db.ReferenceProperty(User, collection_name='modPoints')
        

class Mypage(db.Model):
    creator = db.ReferenceProperty(User)
    date = db.DateTimeProperty(auto_now_add=True)
    header = db.StringProperty()
    subtitle = db.StringProperty()
    blurb = db.TextProperty()
    def get_url(self):
        return hank['domainstring']+'user/'+self.username+'/'
    
class Tag(db.Model):
    """ Tags should be instantiated with their title as a key_name """
    parent_tag = db.SelfReferenceProperty(collection_name='children')
    title = db.StringProperty()
    ancestors = db.StringListProperty()
    descendants = db.StringListProperty()
    
    def set_descendants(self,passive=False):
        descendants = []            
        for child in self.children:
            family = child.set_descendants(True)
            descendants.extend(family)
        if passive:
            descendants.append(self.title)
            return descendants
        else:
            self.descendants = descendants
            self.put()
        
    
    def get_ancestors(self):
        return [Tag.get_by_key_name(title) for title in self.ancestors]
    
    def set_ancestors(self, ancestry = None):
        if not ancestry:
            if self.parent_tag:              
                ancestry = [self.parent_tag.title]
                return self.set_ancestors(ancestry)
            else:
                self.ancestors = []
                self.put()
        else:
            if Tag.get_by_key_name(ancestry[-1]).parent_tag:
                ancestry.append(Tag.get_by_key_name(ancestry[-1]).parent_tag.title)
                return self.set_ancestors(ancestry)
            else:
                self.ancestors = ancestry
                self.put()
        
        
    def get_children(self):
        children = Tag.all().filter('parent_tag ==',self).fetch(1000)
        return children
    
    def get_childNames(self):
        children = Tag.all().filter('parent_tag ==',self).fetch(1000)
        returnChildren = [child.title for child in children]
        return returnChildren
                
    def populate_descendants(self, descendants = None):
        if not descendants:
            descendants = [self.title]
            if self.children:
                for child in self.children:
                    descendants.extend(populate_descendants(child))
                return descendants
            else:
                return descendants
        self.put()
            
    def get_documents(self, own = False):
        
        if self.title == 'Root':
            #return Document.all().filter("draft ==",False).filter('special==',False).order('-date').fetch(1000)
            return get_documents()
        else:
            if own:
                return get_documents([self.title])
            
            else: 
                docs = []
                for descendant in self.descendants:
                     tag = Tag.get_by_key_name(descendant)
                     docs.extend(tag.get_documents(True))
                docs.extend(self.get_documents(True))
                unique = list(set(docs))
                ordered = sorted(unique, key=lambda document: document.date, reverse=True)
                return ordered
            
    def exterminate(self):
        references = Document.all().filter('tags =', self.title).fetch(1000)
        for reference in references:
            #next two line ensure no duplicate version of tag will remain
            purge = remove_duplicates(reference.tags)
            reference.tags = purge
            reference.tags.remove(self.title)
            reference.put()
        children = self.children
        for child in children:
            child.exterminate()
        self.delete()
        
    def get_url(self):
        return '/tag/'+self.title+'/'
        
class Vote(db.Model):
    user = db.ReferenceProperty(User, collection_name='ratings')
    date = db.DateTimeProperty(auto_now_add=True)
    value = db.IntegerProperty()
    current_rating = db.IntegerProperty()
    
    
class VoteDocument(Vote):
    document = db.ReferenceProperty(Document, collection_name='ratings')
    type = db.StringProperty(default = 'document')
    
class VoteComment(Vote):
    comment = db.ReferenceProperty(Comment, collection_name='ratings')
    modifier = db.StringProperty(default=None)
    type = db.StringProperty(default = 'comment')     
    

 
####################################################   
####################################################
# BEGIN REQUEST HANDLERS                           #
####################################################
####################################################

class AJAX(webapp.RequestHandler):
    
    def get(self,request):
        if request == 'getWorks':
            self.getWorks()
    
    def post(self,request):
        #routes requests for information
        if request == 'rate':
            self.rate()
        if request == 'subscribe-query':
            self.subscribeQuery()
        if request == 'delete-comment':
            self.deleteComment()        
            
    def deleteComment(self):
        selfKey = self.request.get('selfKey')
        comment = db.get(selfKey)
        comment.remove()
        
    def getWorks(self):
        user = get_user()
        obj = {}
        works = []
        for document in user.works:
            works.append(document.filename)
        obj['works']=works
        jsonObj = json.dumps(obj)
        self.response.out.write(jsonObj)
                  
    def rate(self):
        """ This code also occurs in Rating. Changes here must be duplicated there.
        Should be unified somehow."""
        
        user = get_user()
        rating = self.request.get('rating')
        key = self.request.get('key')

        object = db.get(db.Key(key))
        if object.object_type == 'Comment':
            vote = VoteComment()
            vote.comment = object
            if not user.is_admin():
                user.useModPoint()
        if object.object_type == 'Document':
            vote = VoteDocument()
            vote.document = object

        if not user.username in object.raters or user.is_admin():
            vote.user = user
            
            if not (user.username in object.raters or user == object.author or not user) or user.is_admin():   
                if rating == "up":
                    if object.object_type == 'Comment' and object.rating >= 5:
                        vote.value = 0
                    else:
                        vote.value = 1
                else:
                    if object.object_type == 'Comment' and object.rating <= -1:
                        vote.value = 0
                    else:
                        vote.value = -1
                    
                object.raters.append(user.username)
                vote.current_rating = object.rating
                vote.put()
                object.set_rating()
                object.author.set_reputation()
                object.author.put()
                object.put()
        self.response.out.write(object.rating)
    
    def subscribeQuery(self):
        user = get_user()
        selfKey = self.request.get('selfKey')
        comment = db.get(selfKey)
        if user.username in comment.subscribers:
            isSubscribed = 'true'
        else: 
            isSubscribed = 'false'
        logging.info('subscribed? '+isSubscribed)
        self.response.out.write(isSubscribed)
        
        
class baseHandler(webapp.RequestHandler):
    
    def get(self,*args):
        if self.usernameCheck():
            self.myGet(*args)
    
    def post(self,*args):
        if self.usernameCheck():
            self.myPost(*args)
    
    def boot(self):
        self.redirect('/')
    
    def nonUserBoot(self):
        user = get_user()
        if not user:
            self.boot()
        
    def usernameCheck(self):
        googleUser = users.get_current_user()
        user = get_user()
        if user and not user.username or googleUser and not user:
            self.redirect('/register')
            return False

        return True
      
    def admincheck(self): 
        user = get_user()
        try:
            if user.is_admin():
                return True
            else:
                return False
                self.boot()
        except:
            return False
            self.boot()
      
class AddTag(baseHandler):
      
    def myGet(self, tag, docName):
        user = get_user() 
        document = get_document(user.username,docName)
        tagObj = Tag.all().filter('title ==',tag)[0]
        self.render(tagObj,document)
        
    def myPost(self, tag, docName):
        user = get_user() 
        added = self.request.get('added')
        request = self.request.get('request')
        tagObj = Tag.all().filter('title ==',tag)[0]
        if Tag.all().filter('title ==',added)[0]: 
            document = get_document(user.username,docName)
            if request == 'add':
                message = document.add_tag(added)
            if request == 'remove':
                message = document.remove_tag(added)
                
            self.render(tagObj,document,message)
        else:
            self.render(tagObj,document,'Tag does not exist.')
        
    def render(self, tag, document,message=None):    
        user = get_user()           
        context = {
                   'baseTag':   tag,
                   'message':   message,
                   'document':  document,
                   'user':      user,
                   'login':     users.create_login_url(self.request.uri),
                   'logout':    users.create_logout_url(self.request.uri)
                   }  
        tmpl = path.join(path.dirname(__file__), 'templates/addTags.html')
        self.response.out.write(template.render(tmpl, context))      
    
class Admin(baseHandler):
    def myGet(self):
        user = get_user()
        if self.admincheck():
            accounts = User.all().fetch(1000)
            context = {
                       'accounts':     accounts,
                       'user':      user,
                       'login':     users.create_login_url(self.request.uri),
                       'logout':    users.create_logout_url(self.request.uri)                       
                       }     
            tmpl = path.join(path.dirname(__file__), 'templates/admin.html')
            self.response.out.write(template.render(tmpl, context)) 
        else:
             self.boot()      
        
class Circle(baseHandler):
    
    def myGet(self,request,data):
        user = get_user()
        
        if request == 'accept':
            user.acceptInvitation(data)
            self.redirect('../../../')
            
        if request == 'clear':
            user.invitations = []
            user.circle = []
            user.circlepermissions = []
            user.invitees = []
            for message in user.streamMessages:
                message.delete()
            user.put()
            self.redirect('../../../')
            
        if request == 'decline':
            user.declineInvitation(data)
            self.redirect('../../../')
        
        if request == 'invite':
            user.invite(data) 
            self.redirect('../../../')
            
        if request == 'leave':
            user.leaveCircle(data)
            self.redirect('../../../')
            
        if request == 'manage':
            context = {
                   'user':      user,
                   'login':     users.create_login_url(self.request.uri),
                   'logout':    users.create_logout_url(self.request.uri)                       
                   }     
            tmpl = path.join(path.dirname(__file__), 'templates/circle.html')
            self.response.out.write(template.render(tmpl, context)) 
            
        if request == 'remove':
            user.removeCircle(data)
            self.redirect('../../../')
            
            
        if request == 'withdraw':
            user.withdrawCircle(data)
            self.redirect('../../../')

class CommentPage(baseHandler):
    def showForm(self,messages=None):
        user = get_user()   
        aboveKey = self.request.get('aboveKey')
        selfKey = self.request.get('selfKey')  
        if aboveKey:
            above = db.get(aboveKey)
        if selfKey:
            selfComment = db.get(selfKey)
            if selfComment.above:
                above = selfComment.above
            elif selfComment.article:
                above = selfComment.article
            elif selfComment.user_page:
                above = selfComment.user_page
        context = {
                'messages': messages,
                'above': above,
                'user':      user,
                'login':     users.create_login_url(self.request.uri),
                'logout':    users.create_logout_url(self.request.uri)
               }   
 
        try:
            context['selfComment']=selfComment
        except:
            pass     
 
        tmpl = path.join(path.dirname(__file__), 'templates/postcomment.html')
        self.response.out.write(template.render(tmpl, context)) 
        
class CommentHandler(CommentPage):
       
    def myPost(self):

        user = get_user()  
        aboveKey = self.request.get('aboveKey')
        selfKey = self.request.get('selfKey')
        delete = self.request.get('delete')
        content = self.request.get('content')
        scriptless = self.request.get('scriptless')
        subject = self.request.get('subject')

        if aboveKey:
            above = db.get(aboveKey)
        if selfKey:
            selfComment = db.get(selfKey)
            
        
        if delete == 'true':
            self.back(selfComment)
            selfComment.remove()

            #context={}
            #tmpl = path.join(path.dirname(__file__), 'templates/empty.html')
            #self.response.out.write(template.render(tmpl, context))
            
        else:            
            try:
                comment = selfComment
            except:
                comment = Comment()                           
                if above.object_type == 'Comment': 
                    comment.above = above              
                if above.object_type == 'Document':
                    comment.article = above                       
                if above.object_type == 'User': 
                    comment.user_page = above
              
            subscribe = self.request.get('subscribe')
            
            if user:
                if subscribe == 'subscribe':
                    comment.subscribe(user)
                else:
                    comment.unsubscribe(user)
            
            if user:
                if user.username:
                    comment.author = user
                    commenter = user.username
            else:
                commenter = 'anonymous'
                
            comment.content = content
            comment.subject = subject
            comment.get_stripped()
            if scriptless == 'true':
                comment.content = comment.stripped_content
            
            try:
                if comment.get_page_object().draft:
                    comment.draft=True                    
            except: 
                pass
            
            comment.put()
            if self.validate(comment,scriptless):
                self.email(selfKey, user, comment)
                self.back(comment)
            
    def email(self, selfKey, user, comment):
            if user:
                for subscriber in comment.author.subscribers_comment:
                    sub = get_user(subscriber)
                    mail.send_mail(
                        'postmaster@essayhost.appspotmail.com',
                        sub.google.email(),
                        'New Comment by %s' % comment.author.username,
                        messages.email_comment(comment),
                        html = messages.email_comment_html(comment)
                        )
            if comment.above :
                if comment.above.subscribers:
                    for subscriber in comment.above.subscribers:
                        sub = get_user(subscriber)
                        mail.send_mail(
                            'postmaster@essayhost.appspotmail.com',
                            sub.google.email(),
                            'New reply to %s' % comment.above.subject,
                            messages.email_comment(comment),
                            html = messages.email_comment_html(comment)
                            )               
            if is_document(comment.get_page_object()):
                if comment.get_page_object().subscribers:
                    for subscriber in comment.get_page_object().subscribers:
                        sub = get_user(subscriber)
                        mail.send_mail(
                            'postmaster@essayhost.appspotmail.com',
                            sub.google.email(),
                            'New reply to %s' % comment.get_page_object().title,
                            messages.email_comment(comment),
                            html = messages.email_comment_html(comment)
                        )  
    def back(self, comment):
        self.redirect(comment.get_page_object().get_url())
        
    def validate(self,comment,scriptless):
        commentCondensed = cleaner(comment.content,string.whitespace)
        pageObject = comment.get_page_object()
        messages = []
        if scriptless:
            comment.parse()
        if not commentCondensed:
            messages.append('A comment must include some content. Please type something.')
        if not comment.subject:
            fallback_subject=''
            if hasattr(pageObject,'subject'):
                fallback_subject = comment.above.subject
            if hasattr(pageObject,'username'):
                fallback_subject = pageObject.username   
            if hasattr(pageObject,'authorname'):
                fallback_subject = pageObject.title
            comment.subject = 'RE:'+ fallback_subject
            comment.put()

        if messages:
            self.showForm(messages)
            return False
        else:
            return True
            

            

class Create_Document(baseHandler):
    """handles new documents and edits"""
    def myGet(self,request):
        user = get_user()
        if user:
            self.getMain(request, user)
        else:
            self.boot()
            
    def getMain(self,request, user):
        self.nonUserBoot()
        user = get_user()
        userdocuments = user.works
        
        if request == "document":
        
            context = {
                       'documentType':request,
                       'userdocuments':userdocuments,
                       'user':      user,
                       'login':     users.create_login_url(self.request.uri),
                       'logout':    users.create_logout_url(self.request.uri)
                       }     
            tmpl = path.join(path.dirname(__file__), 'templates/create.html')
            self.response.out.write(template.render(tmpl, context))   
            
        else:
            context = {
                       'documentType':request,
                       'userdocuments':userdocuments,
                       'user':      user,
                       'login':     users.create_login_url(self.request.uri),
                       'logout':    users.create_logout_url(self.request.uri)
                       }     
            tmpl = path.join(path.dirname(__file__), 'templates/ticket.html')
            self.response.out.write(template.render(tmpl, context))               
        
    def myPost(self,request):
        user = get_user()
        if user:
            self.postDocument(request,user)
        else:
            self.boot()
            
    def postDocument(self, request, user):
        new = False
        existing_filename = self.request.get('existing_filename')
        filename = self.request.get('filename')
        filename = cleaner(filename)
        subscribe = self.request.get('subscribe')
        description = self.request.get('description')
        description = cleaner(description,deletechars = '`~@#^*{[}]|/><)')
        username = self.request.get('username')
        draft = self.request.get('draft')
        scriptless = self.request.get('scriptless')
        documentType = self.request.get('documentType')
        
        # username only gets passed on an edit
        if username:
            document = get_document(username,existing_filename)
        else:
            new = True
            # if new document uses existing filename this will happen
            if get_document(user.username,filename):
                document = get_document(user.username,filename)
            else:
                document = Document()
        
        if subscribe == 'subscribe':
            document.set_subscriber(user.username)
        else:
            document.set_subscriber(user.username,False)
        
        #################################################
        # Handling Tags
        
        tags = self.request.get_all('added_tag')
        document.add_tags(tags)
        
        # End Tags
        ######################################################
        
        if user:
            if user.username:
                document.author = user
                document.authorname = user.username 
            else:
                error = 'Must Be Logged In to Create Documents'
            
        document.content = self.request.get('document_content')
        title = escape(self.request.get('title'))
        document.title = title
        document.subtitle = escape(self.request.get('subtitle'))
        if filename:
            document.filename = filename
        document.set_description(description)
        document.type.append(documentType)
        if draft == 'True':
            document.draft = True
        else:
            if document.draft == True:
                new = True
            document.draft = False
        if scriptless:
            self.validate(document)
        if documentType == 'feature' or documentType == 'bug':
            document.special = True
            document.filename = str(document.key())
            self.makeTicket(document,user)
        document.put()         
       
        if new and not document.draft:
            for subscriber in user.subscribers_document:
                sub = get_user(subscriber)
                mail.send_mail(
                    'postmaster@essayhost.appspotmail.com',
                    sub.google.email(),
                    'New document by %s' % document.authorname,
                    messages.email_document(document),
                    html = messages.email_document_html(document)
                )
        if scriptless == 'true' and documentType == 'document':
            self.redirect('/addtag/Root/'+document.filename+'/')
        else:
            self.redirect('/' + document.authorname + '/document/'+  document.filename + '/')
      
    def makeTicket(self, document,user):
        ticket = Ticket()
        ticket.user = user
        ticket.report = document
        ticket.put()
            
    def validate(self, document):
        document.parse()

class DeleteAccount(baseHandler):
    
    def myPost(self):
        user = get_user()
        username = self.request.get('username')
        verify = self.request.get('delete')
        
        if not (user.username == username or user.is_admin):
            self.boot()
        else:
            if verify == 'true':
                self.deleteAccount(verify)
            else:
                self.verify()
                
    def verify(self):
        user = get_user()
        username = self.request.get('username')        
        context = {
                   'username':  username,
                   'user':      user,
                   'login':     users.create_login_url(self.request.uri),
                   'logout':    users.create_logout_url(self.request.uri)
                   }     
        tmpl = path.join(path.dirname(__file__), 'templates/delete-account.html')
        self.response.out.write(template.render(tmpl, context))       
        
    def deleteAccount(self,verify):
        username = self.request.get('username')
        if verify == 'true':
            user = get_user(username)
            user.remove()
            self.redirect(users.create_logout_url('/home')) 
        
class Delete_Document(baseHandler):
    def myGet(self,name,filename):
        document = get_document(name,filename)
        document.remove()
        self.redirect('/user/' + name + '/')
              
class Edit_Document(baseHandler):
    def myGet(self,name,filename):
        user = get_user()
        userdocuments = user.works
        document = get_document(name, filename)
        added_tags = [Tag.get_by_key_name(title) for title in  document.tags]
        
        commentary = Commentary(user.username,document.filename)
        
        context = {
                   'rating_threshold': 1,
                   'commentary': commentary,
                   'userdocuments':userdocuments,
                   'added_tags':added_tags,
                   'document':  document,
                   'user':      user,
                   'login':     users.create_login_url(self.request.uri),
                   'logout':    users.create_logout_url(self.request.uri)
                   }     
        tmpl = path.join(path.dirname(__file__), 'templates/create.html')
        self.response.out.write(template.render(tmpl, context))
        
class Favorite(baseHandler):
    def myPost(self,user,filename):
        document = get_document(user,filename)
        user = get_user()
        user.add_favorite(document)
      
class Home(baseHandler):
    
    def myGet(self):
        
        if self.request.path != '/home':
            self.redirect('/home')
        user = get_user()
        #if users.get_current_user():
        #    if not user or not user.username:
        #        self.redirect('/register')
        main_documents = get_documents(type='not_meta')
        meta_documents = get_documents(type='meta')
        root = Tag.get_by_key_name('Root')
        root_tags = Tag.all().filter('parent_tag ==',root).fetch(1000)
        context = {
                   'root_tags': root_tags,
                   'meta_documents': meta_documents,
                   'main_documents': main_documents,
                    'user':      user,
                   'login':     users.create_login_url(self.request.uri),
                   'logout':    users.create_logout_url(self.request.uri)                       
                   }     
        tmpl = path.join(path.dirname(__file__), 'templates/home.html')
        self.response.out.write(template.render(tmpl, context))   
        
class Invite(baseHandler):
    def myPost(self):
        
        user = get_user()
        invitee = self.request.get('invitee')
        invited = get_user(invitee)
        user.invitees.append(invitee)
        invited.invitations.append(user.username)
        user.put()
        invited.put()
        
class Invite_Handler(baseHandler):
    def myPost(self):
        user = get_user()
        accept = self.request.get('accept')
        inviter = self.request.get('inviter')
        user.invitations.remove(inviter)
        requester = get_user(inviter)
        requester.invitees.remove(user.username)
        if accept == 'True':         
            user.circlepermissions.append(inviter)            
            requester.circle.append(user.username)
        user.put()
        requester.put()
        
class Message(baseHandler):
    def myGet(self,request,key):
        user = get_user()
        message = db.get(key)
        if request == 'remove':
            if message.recipient.username == user.username:               
                message.remove() 
        self.redirect('../../../')

class Meta(baseHandler):
    def myGet(self):
        user = get_user()
        metaDocs = get_documents(['Meta'])
        featureRequests = get_documents(specialType='feature')
        bugReports = get_documents(specialType='bug')
        context = {
                   'bugReports': bugReports,
                   'featureRequests': featureRequests,
                   'metaDocs':  metaDocs,
                   'user':      user,
                   'login':     users.create_login_url(self.request.uri),
                   'logout':    users.create_logout_url(self.request.uri)                       
                   }     
        tmpl = path.join(path.dirname(__file__), 'templates/meta.html')
        self.response.out.write(template.render(tmpl, context))           

class PostComment(CommentPage):
    def post(self):
        self.showForm()        
        
class Rating(baseHandler):
    """ This code also occurs in AJAX/rate. Changes here must be duplicated there.
    Should be unified somehow."""    
    def myPost(self):
        
        user = get_user()
        rating = self.request.get('rating')
        key = self.request.get('key')
        scriptless = self.request.get('scriptless')
        object = db.get(key)
        if object.object_type == 'Comment':
            vote = VoteComment()
            vote.comment = object
            if not user.is_admin():
                user.useModPoint()
        if object.object_type == 'Document':
            vote = VoteDocument()
            vote.document = object
        if not user.username in object.raters or user.is_admin():
            vote.user = user
            
            if not (user.username in object.raters or user == object.author or not user) or user.is_admin():
                if rating == "up":
                    if object.object_type == 'Comment' and object.rating >= 5:
                        vote.value = 0
                    else:
                        vote.value = 1
                else:
                    if object.object_type == 'Comment' and object.rating <= -1:
                        vote.value = 0
                    else:
                        vote.value = -1
                    
                object.raters.append(user.username)
                vote.current_rating = object.rating
                vote.put()
                object.set_rating()
                object.author.set_reputation()
                object.author.put()
                object.put()
        if scriptless == 'true':
            self.redirect(object.get_url())

        else:     
            rate_level = object.rating
            context = {
                'rating':    rate_level,
                'user':      user,
                'login':     users.create_login_url(self.request.uri),
                'logout':    users.create_logout_url(self.request.uri)
               }  
            tmpl = path.join(path.dirname(__file__), 'templates/rated.html')
            self.response.out.write(template.render(tmpl, context))  
        
class ReplyBase(baseHandler):
    def myPost(self):
        user = get_user()
        key = self.request.get('key')
        above = Comment.get(db.Key(key))
        commentType = self.request.get('commentType')
        filename = self.request.get('filename')
        object_user = self.request.get('object_user')
        context = {
                   'above': above,
                   'user': user,
                   'key':key,
                   'commentType': commentType,
                   'login':     users.create_login_url(self.request.uri),
                   'logout':    users.create_logout_url(self.request.uri)
                   }
        if filename:
            document = get_document(object_user, filename)
            context['document'] = document
        else:
            page_user = get_user(object_user)
            context['page_user'] = page_user
        tmpl = path.join(path.dirname(__file__), 'templates/reply-base.html')
        self.response.out.write(template.render(tmpl, context))
        
class Register(webapp.RequestHandler):
     
    def get(self):  
         
        user = get_user()   
        if user:
            if user.username:
                self.redirect('/home')
        else:
            if not users.get_current_user():
                self.redirect(users.create_login_url(self.request.uri))
            else:
                self.registerPage()
            
    def post(self):
        cancel = self.request.get('cancel')
        if cancel:
            self.redirect(users.create_logout_url('/home')) 
        else:
            user = get_user()   
            if user:
                if user.username:
                    self.redirect('/home')
            else:
                if not users.get_current_user():
                    self.redirect(users.create_login_url(self.request.uri))
                else:
                    self.recieveData()
                
    def recieveData(self):
        user = get_user()
        scriptless = self.request.get('scriptless')
        hold = False
        user =User()
        user.google = users.get_current_user() 
        messages = []
        changed = None
        taken = None
        
        #remove unacceptable characters
        name = self.request.get('username')
        cleanedName = cleaner(name)
        
        if cleanedName != name:
            messages = ['Some unacceptable characters were removed from your username.'] 
            changed = cleanedName
            if scriptless == 'true':
                hold = True
                
        if not cleanedName:
            messages.append('A username must contain some characters.')
            hold = True
            
        if not get_user(cleanedName.lower()):
            user.username = cleanedName.lower()
        else: 
            messages.append('This username is already in use.')
            taken = True
            hold = True
            
        if hold:
            self.registerPage(messages, changed, taken)
        else:
            user.put()
            self.redirect('/home')
                    
    def registerPage(self,messages=None, changed=False, taken = False):
        user = get_user()
        context = {
                'taken':     taken,
                'messages':  messages,
                'changed':   changed,
                'user':      user,
                'login':     users.create_login_url(self.request.uri),
                'logout':    users.create_logout_url(self.request.uri)                       
                }     
        tmpl = path.join(path.dirname(__file__), 'templates/register.html')
        self.response.out.write(template.render(tmpl, context))
        
class Subscription_Handler(baseHandler):
             
    def myPost(self, username):
        user = get_user()
        subscriptions = self.request.get_all('subscriptions')
        user.set_subscription(subscriptions,username)
        self.redirect('../../')
        #self.response.out.write(message)
  
class Subscribe_Tag(webapp.RequestHandler):
    
    def get(self, scriptless, request, tagTitle):
        self.makeRequest(request, tagTitle)
        if scriptless:
            self.redirect('../../../')

    def makeRequest(self,request, tagTitle):
        user = get_user()
        if request == 'add':
            user.subscribeTag(tagTitle, True)
        if request == 'remove':
            user.subscribeTag(tagTitle, False)
        

      
class Tag_Browser(webapp.RequestHandler):
    def post(self):
        months = ['Jan.','Feb.','Mar.','Apr.','May','Jun.','Jul.','Aug.','Sep.','Oct.','Nov.','Dec.']
        focal = self.request.get('tag')
        obj = {}
        #if focal != 'root':
        focalTag = Tag.get_by_key_name(focal)
        obj['focal_tag']=focalTag.title
        obj['path']=focalTag.ancestors
        obj['children']=focalTag.get_childNames()
                       
        docs=focalTag.get_documents()
       # else:
            #obj['children']=[child.title for child in Tag.all().filter('parent_tag ==',None).fetch(1000)]
            #obj['focal_tag']=None
            #obj['path']=None
            
            #docs = get_documents()
        documents = []
        for doc in docs:
            newDoc = {}
            newDoc['title']=str(doc.title)
            newDoc['description']=doc.get_description()
            newDoc['author']=doc.authorname
            newDoc['date']=months[doc.date.month-1]+' '+str(doc.date.day)+', '+str(doc.date.year)
            newDoc['filename']=doc.filename
            newDoc['key']=str(doc.key())
            documents.append(newDoc)
        obj['documents']=documents
        jsonObj = json.dumps(obj)

            
        self.response.out.write(jsonObj)
        
class TagManager(baseHandler):
    def myPost(self, request):
        user = get_user()            
        if request == 'create':
            if self.admincheck():
                create_title = cleaner(self.request.get('new_title').replace(' ','_'))
                parent_title = self.request.get('parent_title')
                tag = Tag(key_name=create_title)
                tag.title = create_title
                if parent_title:
                    tag.parent_tag = Tag.get_by_key_name(parent_title)
                else:
                    if Tag.get_by_key_name('Root'):
                        tag.parent_tag = Tag.get_by_key_name('Root')
                    else:
                        root = Tag(key_name='Root')
                        root.title = 'Root'
                        for item in Tag.all().filter('parent_tag ==',None).fetch(1000):
                            item.parent_tag = root
                            item.set_ancestors()
                            item.put()
                        root.set_ancestors()
                        root.set_descendants()
                        root.put()
                        tag.parent_tag = root
                            
                tag.set_ancestors()
                tag.set_descendants()
                tag.put() 
                    
                if user.is_admin():
                    user_type='admin' 
                if parent_title:              
                    parent = tag.parent_tag
                    tags = parent.children.order('title')
                        
                    context = {
                        'user':     user,
                        'parent':   parent,
                        'user_type':user_type,
                        'tags':     tags,
                        'parent_title':    parent.title,
                       }  
                    tmpl = path.join(path.dirname(__file__), 'templates/tag_request/expand.html')
                    self.response.out.write(template.render(tmpl, context))  
                else:
                    root_tags = Tag.all().filter('parent_tag ==', None).fetch(100)
                    context = {
                               'user':     user,
                                'user_type':user_type,
                               'tags': root_tags,
                               }
                    tmpl = path.join(path.dirname(__file__), 'templates/tag_request/base.html')
                    self.response.out.write(template.render(tmpl, context))
                
        if request == 'newform':
            new_title = self.request.get('title')
            context = {
                'parent_title':      new_title,
               }  
            tmpl = path.join(path.dirname(__file__), 'templates/tag_request/newform.html')
            self.response.out.write(template.render(tmpl, context))
                
        if request == 'expand':
    
            user_type = self.request.get('user_type')
            expand_title = self.request.get('title')
            parent = Tag.get_by_key_name(expand_title)
            tags = parent.children.order('title')
            context = {
                'user':     user,
                'parent':   parent,
                'user_type':user_type,
                'tags':     tags,
                'parent_title':    expand_title,
               }  
            tmpl = path.join(path.dirname(__file__), 'templates/tag_request/expand.html')
            self.response.out.write(template.render(tmpl, context))    
                
        if request == 'contract':
            if self.request.get('destination'):
                destination = self.request.get('destination')
            else:
                destination = 'empty.html'
            context = {}
            tmpl = path.join(path.dirname(__file__), 'templates/tag_request/' + destination)
            self.response.out.write(template.render(tmpl, context))  
                
        if request == 'addto':
            added_tags_pre = self.request.get('added_tags')
            added_tags = [Tag.get_by_key_name(title) for title in  eval(added_tags_pre)]
            context = {'added_tags':added_tags}
            tmpl = path.join(path.dirname(__file__), 'templates/tag_request/addto.html')
            self.response.out.write(template.render(tmpl, context))  
                
        if request == 'base':
            user_type = self.request.get('user_type')
            root = Tag.all().filter('title ==', 'Root').fetch(1)[0]
            root_tags = root.get_children()
            context = {
                       'user':     user,
                        'user_type':user_type,
                       'tags': root_tags,
                       }
            tmpl = path.join(path.dirname(__file__), 'templates/tag_request/base.html')
            self.response.out.write(template.render(tmpl, context))
                  
        if request == 'remove':
            if self.admincheck():
                removed = self.request.get('title')
                Tag.get_by_key_name(removed).exterminate()
                    
                context = {}
                tmpl = path.join(path.dirname(__file__), 'templates/tag_request/empty.html')
                self.response.out.write(template.render(tmpl, context))
            
class Tag_Page(baseHandler):
    def myGet(self, maintag):
        user = get_user()
        tagobj = Tag.get_by_key_name(maintag)
        tagobj.set_ancestors()
        context = {
               'user': user,
               'maintag':tagobj,
               'login':     users.create_login_url(self.request.uri),
               'logout':    users.create_logout_url(self.request.uri)
               }     
        tmpl = path.join(path.dirname(__file__), 'templates/tag_page.html')
        self.response.out.write(template.render(tmpl, context))  
        
class Tasks(webapp.RequestHandler):
    def get(self, request):
        if request == 'modPoints':
            self.modPoints()
            
    def modPoints(self):
        period = datetime.datetime.now()-datetime.timedelta(hours=6)
        weekAgo = datetime.datetime.now()-datetime.timedelta(weeks=1)
        
        newDocs = get_documents(since=period)
        newComments = Comment.all().filter('date >=',period).fetch(1000)       
                
        users = User.all().fetch(1000)
        
        # remove unused modpoints and add to allocation pool
        recycledPoints = 0
        oldPoints = ModPoint.all().filter('date <=',weekAgo)       
        for point in oldPoints:
            recycledPoints += 1
            point.delete()
                    
        # one mod point per comment + recycleds
        newModPoints = len(newComments) + recycledPoints
        
        allocationFunction = [0]
        i=0
        #build reputation function
        while(i<len(users)):
            logging.info('i = '+ str(i))
            allocationFunction.append(users[i].reputation + allocationFunction[i])
            i+=1
        #assign mod points to users
        while(newModPoints>0):
            x = random.uniform(0,1)
            FofX = x*allocationFunction[-1]
            for index, y in enumerate(allocationFunction):
                if FofX <= y:
                    if not users[index-1].is_admin(): # admins do not need modpoints
                        users[index-1].addModPoint()
                        newModPoints -= 1
                    break
                    

                    
            
        #for user in users:
        #   user.set_reputation()
        
        #for user in users:
        #    user.set_modpoints()
        
    
class Update_Model(baseHandler):
    
    def myPost(self):
        modelClass = self.request.get('modelClass')
        
        if not modelClass:
            modelClass = hank['updatingModel']
            self.update(modelClass)
        else:            
            test = eval(modelClass+'()')
            hank['updatingModel'] = modelClass
            if self.admincheck():
                self.update(modelClass)
            #except:
             #   logging.info(modelClass+' does not appear to be a real class')
              #  #should return 'no such class' message here
               # self.boot()
                
    def update(self, modelClass):
        attrValue = self.request.get('attrValue', None)
        attr = self.request.get('attr', None)
        
        if attrValue is None:
            # First request, just get the first name out of the datastore.
            obj = eval(modelClass+".gql('ORDER BY "+attr+" DESC').get()")
            logging.info('obj = '+str(obj))
            attrValue = eval("obj."+attr)
        
        q = eval(modelClass+".gql('WHERE "+attr+" <= :1 ORDER BY "+attr+" DESC', '"+attrValue+"')") 
        
        objs = q.fetch(limit=2)
        current_obj = objs[0]
        if len(objs) == 2:
            next_attrValue = eval("objs[1]."+attr)
            next_url = '/update-model?attrValue=%s' % urllib.quote(next_attrValue)
        else:
            hank['updatingModel'] = None
            next_attrValue = 'FINISHED'
            next_url = '/'  # Finished processing, go back to main page.
        
        #if additional processing were necessary it would go here
        current_obj.put()
        
        context = {
            'current_obj': obj,
            'next_obj': next_attrValue,
            'next_url': next_url,
        }
        tmpl = path.join(path.dirname(__file__), 'templates/update-model.html')
        self.response.out.write(template.render(tmpl, context))


class UserBase(baseHandler):
    def myGet(self,username):
        user = get_user()
        creator = get_user(username)
        context = {
                'pageObject': creator,
                'commentary':creator.get_commentary(),
                'commentType': 'userpage',
                'page_user': creator,
                'user': user,
                'login':     users.create_login_url(self.request.uri),
                'logout':    users.create_logout_url(self.request.uri)
               }     
        tmpl = path.join(path.dirname(__file__), 'templates/user_base.html')
        self.response.out.write(template.render(tmpl, context))
        
class UserInfo(baseHandler):
    def myPost(self):
          firstname = self.request.get('firstname')
          lastname = self.request.get('lastname')
          threshold = self.request.get('threshold')
          displayname = self.request.get('displayname')
          
            
class Username_Check(webapp.RequestHandler):
    def post(self):
        username = self.request.get('username')
        if username:
            if get_user(username.lower()):
                self.response.out.write('00')
            elif username != cleaner(username):
                self.response.out.write('01')
            else:
                self.response.out.write('1')
        else:
                self.response.out.write('02')
                
class UserPage(baseHandler):
    def myGet(self, page_user):
        creator = get_user(page_user)
        user = get_user()
        creator.set_reputation()
        context = {
                   'pageObject': creator,
                   'commentType': 'userpage',
                   'rating_threshold': 1,
                   'commentary':creator.get_commentary(),
                   'page_user': creator,
                   'user':      user,
                   'login':     users.create_login_url(self.request.uri),
                   'logout':    users.create_logout_url(self.request.uri)
                   }     
        tmpl = path.join(path.dirname(__file__), 'templates/user.html')
        self.response.out.write(template.render(tmpl, context))   
  
class View_Document(baseHandler):
    
    def myGet(self, name, filename, reply_id=None):
        
        user = get_user()
        document = get_document(name, filename)
        
        if document.draft and not user:
            self.boot()
        else:
            if document.draft and not (user.username == document.author.username or user.username in document.author.circle):
                self.boot()
            else:            
                document.set_view()        
        
                context = {
                    'commentType': 'document',
                    'rating_threshold': 1,
                    'commentary': document.get_commentary(),
                    'pageObject': document,
                    'document': document,
                    'filename': filename,
                    'name':     name,
                    'user':      user,
                    'login':     users.create_login_url(self.request.uri),
                    'logout':    users.create_logout_url(self.request.uri)
                }
                tmpl = path.join(path.dirname(__file__), 'templates/document.html')
                self.response.out.write(template.render(tmpl, context))  
        

application = webapp.WSGIApplication([
    ('/userinfo/',UserInfo),
    ('/modpoints/(.*)/',Tasks),
    ('/tasks/(.*)/',Tasks),
    ('/ajax/(.*)/',AJAX),
    ('.*/rate/', Rating),
    ('/tag_browser/',Tag_Browser),
    ('.*/tag_(.*)/', TagManager),
    ('.*/subscribe-tag/(.*)_(.*)/(.*)/', Subscribe_Tag),
    ('/reply-base/', ReplyBase),
    ('.*/comment/', CommentHandler),
    ('.*/circle/(.*)/(.*)/', Circle),
    ('/delete-account/', DeleteAccount),
    ('/postcomment/', PostComment),
    ('/addtag/(.*)/(.*)/', AddTag),
    ('/tag/(.+)/',Tag_Page),
    ('/(.*)/document/(.*)/favorite/',Favorite),
    ('.*/subscribe/(.*)/', Subscription_Handler),
    ('/invite_handler/', Invite_Handler),
    ('/invite/', Invite),
    ('/availability/', Username_Check),
    ('/update-model/', Update_Model),  
    ('/meta/',Meta),                                    
    ('/admin/', Admin),
    ('.*/message/(.*)/(.*)/',Message),
    ('/user/(.*)/', UserPage),
    ('/register', Register),
    ('/create/(.*)/', Create_Document),
    (r'/(.*)/document/(.*)/edit/delete/', Delete_Document),
    (r'/(.*)/document/(.*)/edit/', Edit_Document),
    (r'/(.*)/document/(.*)/reply/(.+)', View_Document),  
    (r'/(.*)/document/(.*)/*(.*)/', View_Document),
    (r'/.*', Home),
    ], debug=True)


 
def main():
    run_wsgi_app(application)
    
if __name__ == '__main__':
    main()
    
