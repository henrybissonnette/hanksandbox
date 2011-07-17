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
import os, re, logging, sys,datetime,math
import messages, json

domainstring='http://essayhost.appspot.com/'

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

def get_documents(tag_list=[], tag_not_list=[], number=1000, type=None):
    """ tag_list should be a string list of tags """
        
    document_query = Document.all()
    if type: 
        document_query.filter("type ==",type)
    for tag in tag_list:
        document_query.filter("tags ==",tag)
    for tag in tag_not_list:
        document_query.filter("tags !=",tag)
    documents = document_query.order('-date').fetch(number)
    return documents

def admincheck():
    
    adminlist = ['henrydbissonnette@gmail.com',]
    user = users.get_current_user()
    try:
        if user.email() in adminlist:
            return True
        else:
            return False
    except:
        return False
    
def adminboot():
        admincheck()
        if not user.admin:
            self.redirect('/home/')


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
    if admincheck():
        user.admin = True 
        user.put()
    else:
        user.admin = False 
        user.put()
    
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
       if marker in seen: continue
       seen[marker] = 1
       result.append(item)
   return result


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
        
        document = get_document(username, document_filename)

        if document:
            self.comments = document.comments.order('-date')
        else:      
            self.comments = get_user(username).mypagecomments.order('-date')
            
        self.comment_tree = self.prepare_reply_tree(self.comments)
        self.delta =  self.delta_builder(self.comment_tree[1])  
        self.sum_delta = [1] * sum([item for sublist in self.delta for item in sublist])
        self.keys = [str(comment.key()) for comment in self.comment_tree[0]]   
        self.comment_data = zip(self.comment_tree[0], self.keys, self.delta)


class User(db.Model):
    
    admin = db.BooleanProperty(default=False)
    circle = db.StringListProperty(default=[])
    circlepermissions = db.StringListProperty(default=[])
    date = db.DateTimeProperty(auto_now_add=True)
    displayname = db.StringProperty()
    email_log = db.ListProperty(db.Key,default=[])
    favorites = db.ListProperty(db.Key,default=[])
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
    object_type = db.StringProperty(default = 'User')
    username = db.StringProperty()
    
    def get_age(self):
        age = datetime.datetime.now()-self.date
        return age.days
    
    def add_favorite(self, document):
        if not document.key in self.favorites:
            self.favorites.append(document.key())
        if not self.username in document.favorites:
            document.favorites.append(self.username)
        document.put()
        self.put()
        
    def fetch_favorites(self):
        favorites = []
        for key in self.favorites:
            favorites.append(Document.get(key))
        return favorites
            
    def get_url(self):
        return domainstring+'user/'+self.username+'/'
    
    def drafts(self):
        self.works.filter('draft ==', True)
        
    def publications(self):
        self.works.filter('draft ==', False)
        
    def fetch_stream(self,number=10):

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
            
        ordered = sorted(documents, key=lambda document: document.date, reverse=True)
        return ordered[:number]
    
    def set_reputation(self):
        
        reputation=1
        myworks = self.works.fetch(1000)
        mycomments = self.mycomments
        total_views = 0
            
        for document in myworks:
            reputation = reputation + 4*document.rating
            total_views = total_views + document.views
        
        for comment in mycomments: 
            reputation = reputation + comment.rating
            
        if self.get_age() < 100:
            reputation = reputation*math.sqrt(self.get_age())/10
            
        reputation = (math.sqrt(reputation)/100)*97
            
        prolificity = len(myworks)
        if prolificity >= 1:
            reputation = reputation + 1           
            if prolificity >= 10:
                reputation = reputation + 1
                if total_views/prolificity <= 20:
                    reputation = reputation - 2
                if prolificity >= 30:
                    reputation = reputation + 1 
                    if total_views/prolificity <= 30:
                        reputation = reputation - 2
                        
        self.reputation = int(reputation)    
        self.put()
        

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
    type = db.StringListProperty(default=["not_meta"])
    
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
    
    def get_url(self):
        return domainstring+self.author.username+'/document/'+self.filename+'/'
    
    def get_stripped(self):
        
        stripped = strip_tags(self.content)
        #logging.info('stripped 1: '+stripped)
        #for n in range(len(stripped)):
            #logging.info('n = '+ n)
            #if stripped[n] =='&':
                #logging.info('found')
                #stripped = stripped[:n]+stripped[n+5:]
        #logging.info('stripped 2: '+stripped)
        return stripped
    
    def set_description(self, words):
        words = strip_tags(words)
        words = words[:150]
        self._description=words
        
    def get_description(self):
        return self._description
    
    def get_leaftags(self):
        return [Tag.get_by_key_name(title) for title in self.leaftags]
    
    def set_rating(self):
        votes = self.ratings 
        rating = 0;
        view_mass = 0;
        for viewer in self.viewers:
            user_view = get_user(viewer)
            view_mass =  view_mass + (1+user_view.reputation)
        for vote in votes:
            rating = rating + vote.value*(1+vote.user.reputation)
        rating = rating/view_mass
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
            reply.remove()
            
        self.delete()
        
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
            

class Comment(db.Model):
    """It might also be more elegant to 
    manage depth with a property here."""
    author = db.ReferenceProperty(User, collection_name = 'mycomments')
    raters = db.StringListProperty()
    content = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    draft = db.BooleanProperty(default=False)
    above = db.SelfReferenceProperty(collection_name='replies')
    article = db.ReferenceProperty(Document,collection_name='comments')
    user_page = db.ReferenceProperty(User, collection_name='mypagecomments')
    rating = db.IntegerProperty(default=0)
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
        
    def set_rating(self):
        votes = self.ratings
        rating = 0;
        for vote in votes:
            rating = rating + vote.value*(1+vote.user.reputation)
        self.rating = rating
        self.put()
    
    def remove(self):
        
        ratings = self.ratings
        for rating in ratings:
            rating.delete()
        
        children = self.replies
        for child in children:
            child.remove()
            
        self.delete()

class Mypage(db.Model):
    creator = db.ReferenceProperty(User)
    date = db.DateTimeProperty(auto_now_add=True)
    header = db.StringProperty()
    subtitle = db.StringProperty()
    blurb = db.TextProperty()
    def get_url(self):
        return domainstring+'user/'+self.username+'/'
    
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
            
    def get_documents(self):
        return get_documents([self.title])
            
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
    type = db.StringProperty(default = 'comment')        
    
class Admin(webapp.RequestHandler):
    def get(self):
        user = get_user()
        if user:
            if not user.admin:
                    self.redirect('/home')
        else:
            self.redirect('/home')
        
        context = {
                   'user':      user,
                   'login':     users.create_login_url(self.request.uri),
                   'logout':    users.create_logout_url(self.request.uri)                       
                   }     
        tmpl = path.join(path.dirname(__file__), 'templates/admin.html')
        self.response.out.write(template.render(tmpl, context))   
    

class CommentBox(webapp.RequestHandler):
    
    def post(self):
        user = get_user()
        filename = self.request.get('filename')
        authorname = self.request.get('authorname')
        page_user = self.request.get('page_user')
        document = get_document(authorname,filename)
        context = {
            'page_user':    page_user,
            'authorname':    authorname,
            'document':    document,
            'user':      user,
            'login':     users.create_login_url(self.request.uri),
            'logout':    users.create_logout_url(self.request.uri)
           }  
        tmpl = path.join(path.dirname(__file__), 'templates/comment_request/comment_box.html')
        self.response.out.write(template.render(tmpl, context))        
        

class CommentHandler(webapp.RequestHandler):
    def post(self):
        comment_type = self.request.get('comment_type')
        new = False
        
        if comment_type == 'delete':
            self_key = self.request.get('key')
            comment = db.get(self_key)
            comment.remove()
            context={}
            tmpl = path.join(path.dirname(__file__), 'templates/empty.html')
            self.response.out.write(template.render(tmpl, context))
            
        else: 
            
            if comment_type == 'edit':
                self_key = self.request.get('key')
                comment = db.get(self_key)
            else:
                comment = Comment()             
            # subject handles comment topics
            subject = self.request.get('subject')
            # this if skips the above assignment
            fallback_subject=''
            if comment_type=='edit':
                pass
            else:
                new = True
                # replies to other comments get handled by if
                if comment_type=='reply':
                    above_key = self.request.get('key')
                    comment.above = db.Key(above_key)
                    fallback_subject = comment.above.subject
                # else sticks top level comments to an appropriate object
                else:
                # comments on a document page
                    if 'document' in self.request.uri:
                        filename= self.request.get('filename')
                        name= self.request.get('object_user')
                        article = get_document(name, filename)
                        comment.article = article
                        if not fallback_subject:
                            fallback_subject = article
                 #comments on a user page       
                    if 'user' in self.request.uri:
                        name = self.request.get('object_user')
                        comment.user_page = get_user(name)
                        if not fallback_subject:
                            fallback_subject = name
            if subject:
                comment.subject = subject
            else:
                comment.subject = 'RE:'+ fallback_subject
              
            user = get_user()  
            
            subscribe = self.request.get('subscribe')

            if subscribe == 'subscribe':
                if not user.username in comment.subscribers:
                    comment.subscribers.append(user.username)
            else:
                if user:
                    if user.username in comment.subscribers:
                        comment.subscribers.remove(user.username)
     
            
            if user:
                if user.username:
                    comment.author = user
                    commenter = user.username
            else:
                commenter = 'anonymous'
                
            comment.content = self.request.get('content')
            comment.get_stripped()
            
            try:
                if comment.get_page_object().draft:
                    comment.draft=True
            except: 
                pass
            
            comment.put()
            
            if new:
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
                        
            self.redirect('..')

class Create_Document(webapp.RequestHandler):
    #this get should probably be merged with edit
    def get(self):
        
        user = get_user()
        userdocuments = user.works
        
        context = {
                   'userdocuments':userdocuments,
                   'user':      user,
                   'login':     users.create_login_url(self.request.uri),
                   'logout':    users.create_logout_url(self.request.uri)
                   }     
        tmpl = path.join(path.dirname(__file__), 'templates/create.html')
        self.response.out.write(template.render(tmpl, context))   
        
    def post(self):
        
        user = get_user()
        new = False
        existing_filename = self.request.get('existing_filename')
        filename = self.request.get('filename')
        filename = cleaner(filename)
        subscribe = self.request.get('subscribe')
        description = self.request.get('description')
        description = cleaner(description,deletechars = '`~@#^*{[}]|/><)')
        username = self.request.get('username')
        draft = self.request.get('draft')
        
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
        logging.info('tags: '+str(tags))
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
        document.filename = filename
        document.set_description(description)
        if draft == 'True':
            document.draft = True
        else:
            if document.draft == True:
                new = True
            document.draft = False
        document.put()
       
        if new and not document.draft:
            logging.info('if happened')
            for subscriber in user.subscribers_document:
                sub = get_user(subscriber)
                mail.send_mail(
                    'postmaster@essayhost.appspotmail.com',
                    sub.google.email(),
                    'New document by %s' % document.authorname,
                    messages.email_document(document),
                    html = messages.email_document_html(document)
                )

        self.redirect('/' + document.authorname + '/document/'+  filename + '/')

class Delete_Document(webapp.RequestHandler):
    def get(self,name,filename):
        document = get_document(name,filename)
        document.remove()
        self.redirect('/user/' + name + '/')
              
class Edit_Document(webapp.RequestHandler):
    def get(self,name,filename):
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
        
class Favorite(webapp.RequestHandler):
    def post(self):
        key = self.request.get('document')
        document = Document.get(key)
        user = get_user()
        user.add_favorite(document)
      
class Home(webapp.RequestHandler):
    
    def get(self):
        if self.request.path != '/home':
            self.redirect('/home')
        user = get_user()
        if users.get_current_user():
            if not user or not user.username:
                self.redirect('/register')
        main_documents = get_documents(type='not_meta')
        meta_documents = get_documents(type='meta')
        root_tags = Tag.all().filter('parent_tag ==',None).fetch(1000)
        logging.info('root tags: '+str(root_tags))
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
        
class Invite(webapp.RequestHandler):
    def post(self):
        
        user = get_user()
        invitee = self.request.get('invitee')
        invited = get_user(invitee)
        user.invitees.append(invitee)
        invited.invitations.append(user.username)
        user.put()
        invited.put()
        
class Invite_Handler(webapp.RequestHandler):
    def post(self):
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
        
        
        
class Rating(webapp.RequestHandler):
    
    def post(self):
        
        user = get_user()
        rating = self.request.get('rating')
        key = self.request.get('key')
        username = self.request.get('username')
        filename = self.request.get('filename')
        if key:
            object = Comment.get(db.Key(key))
            vote = VoteComment()
            vote.comment = object
        else:
            object = get_document(username,filename)
            vote = VoteDocument()
            vote.document = object
        if not user.username in object.raters:
            
            vote.user = user
            
            if not (user.username in object.raters or user == object.author or not user):
    
                if rating == "up":
                    vote.value = 1
                else:
                    vote.value = -1
                    
                object.raters.append(user.username)
                vote.current_rating = object.rating
                vote.put()
                object.set_rating()
                object.author.set_reputation()
                object.author.put()
                object.put()
                
            rate_level = object.rating
            context = {
                'rating':    rate_level,
                'user':      user,
                'login':     users.create_login_url(self.request.uri),
                'logout':    users.create_logout_url(self.request.uri)
               }  
            tmpl = path.join(path.dirname(__file__), 'templates/rated.html')
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

        context = {
                    'user':      user,
                    'login':     users.create_login_url(self.request.uri),
                    'logout':    users.create_logout_url(self.request.uri)                       
                    }     
        tmpl = path.join(path.dirname(__file__), 'templates/register.html')
        self.response.out.write(template.render(tmpl, context))
            
    def post(self):
        user = get_user()
        user = User()
        user.google = users.get_current_user()
        name = self.request.get('username')
        name = cleaner(name)
        if not get_user(name.lower()):
            user.username = name.lower()
        user.put()
        self.redirect('/home')
        
class ReplyBox(webapp.RequestHandler):
    
    def post(self):
        # request = edit tells us that its an edit
        request = self.request.get('request')
        user = get_user()
        key = self.request.get('key')
        above = db.get(key)
        context = {
            'above':  above,
            'key':    key,
            'user':      user,
            'login':     users.create_login_url(self.request.uri),
            'logout':    users.create_logout_url(self.request.uri)
           }  
        if request == 'edit':
            edit = db.get(key)
            context['edit']=edit
        tmpl = path.join(path.dirname(__file__), 'templates/comment_request/reply_box.html')
        self.response.out.write(template.render(tmpl, context)) 
        
class Subscription_Handler(webapp.RequestHandler):
             
    def post(self):
        flag=None
        user = get_user()
        subscriptions = self.request.get_all('subscriptions[]')
        page_user = self.request.get('page_user')
        subscribee = get_user(page_user)
        
        if not subscriptions:
            if user.username in subscribee.subscribers:
                    subscribee.subscribers.remove(user.username)

            if subscribee.username in user.subscriptions_user:
                    user.subscriptions_user.remove(subscribee.username)

            message = 'This user has been removed from your subscriptions.'    
        else:
            if user.username not in subscribee.subscribers:
                    subscribee.subscribers.append(user.username)
                    flag = 1

            if subscribee.username not in user.subscriptions_user:
                    user.subscriptions_user.append(subscribee.username)
                    flag = 1
               
        if flag:
            message = 'This user has been added to your subscriptions.' 
        else:
            message = 'Your settings have been saved.'
        
        if 'subscribe_publish' in subscriptions:
            if not page_user in user.subscriptions_document:
                user.subscriptions_document.append(page_user)
        else:
            if page_user in user.subscriptions_document:
                user.subscriptions_document.remove(page_user)
                
        if 'email_publish' in subscriptions:
            if not user.username in subscribee.subscribers_document:
                subscribee.subscribers_document.append(user.username)
        else:
            if user.username in subscribee.subscribers_document:
                subscribee.subscribers_document.remove(user.username)
                
        if 'subscribe_comment' in subscriptions:
            if not page_user in user.subscriptions_comment:
                user.subscriptions_comment.append(page_user)
        else:
            if page_user in user.subscriptions_comment:
                user.subscriptions_comment.remove(page_user)
        
        if 'email_comment' in subscriptions:
            if not user.username in subscribee.subscribers_comment:
                subscribee.subscribers_comment.append(user.username)
        else:
            if user.username in subscribee.subscribers_comment:
                subscribee.subscribers_comment.remove(user.username)
        
        subscribee.put()
        user.put()
        
        self.response.out.write(message)
        
class Tag_Browser(webapp.RequestHandler):
    def post(self):        
        
        focal = self.request.get('tag')
        obj = {}
        if focal != 'root':
            focalTag = Tag.get_by_key_name(focal)
            obj['focal_tag']=focalTag.title
            obj['path']=focalTag.ancestors
            obj['children']=focalTag.get_childNames()
                       
            docs=focalTag.get_documents()
        else:
            obj['children']=[child.title for child in Tag.all().filter('parent_tag ==',None).fetch(1000)]
            obj['focal_tag']=None
            obj['path']=None
            
            docs = get_documents()
        documents = []
        for doc in docs:
            newDoc = {}
            newDoc['title']=str(doc.title)
            newDoc['description']=doc.get_description()
            newDoc['author']=doc.authorname
            newDoc['date']=str(doc.date)
            newDoc['filename']=doc.filename
            newDoc['key']=str(doc.key())
            documents.append(newDoc)
        obj['documents']=documents
        
        logging.info(str(obj))
        jsonObj = json.dumps(obj)

            
        self.response.out.write(jsonObj)
        
class TagManager(webapp.RequestHandler):
    def post(self, request):
        user = get_user()
        #if not user.admin:
            #self.redirect('/home')
         
        if request == 'create':
            create_title = cleaner(self.request.get('new_title').replace(' ','_'))
            parent_title = self.request.get('parent_title')
            tag = Tag(key_name=create_title)
            tag.title = create_title
            if parent_title:
                tag.parent_tag = Tag.get_by_key_name(parent_title)
            tag.set_ancestors()
            tag.set_descendants()
            tag.put() 
            
            if user.admin:
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
            root_tags = Tag.all().filter('parent_tag ==', None).fetch(100)
            context = {
                       'user':     user,
                       'user_type':user_type,
                       'tags': root_tags,
                       }
            tmpl = path.join(path.dirname(__file__), 'templates/tag_request/base.html')
            self.response.out.write(template.render(tmpl, context))
                  
        if request == 'remove':
            removed = self.request.get('title')
            Tag.get_by_key_name(removed).exterminate()
            
            context = {}
            tmpl = path.join(path.dirname(__file__), 'templates/tag_request/empty.html')
            self.response.out.write(template.render(tmpl, context))
            
class Tag_Page(webapp.RequestHandler):
    def get(self, maintag):
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
        
        
            
class Update_Models(webapp.RequestHandler):
    def post(self, request):
        adminboot()
        if request == 'start':
            context = {}
            tmpl = path.join(path.dirname(__file__), 'templates/update_models.html')
            self.response.out.write(template.render(tmpl, context))
            
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
                
class UserPage(webapp.RequestHandler):
    def get(self, page_user):
        creator = get_user(page_user)
        user = get_user()
        essays = creator.works
        commentary = Commentary(page_user)
        context = {
                   'rating_threshold': 1,
                   'commentary':commentary,
                   'essays':    essays,
                   'page_user': creator,
                   'user':      user,
                   'login':     users.create_login_url(self.request.uri),
                   'logout':    users.create_logout_url(self.request.uri)
                   }     
        tmpl = path.join(path.dirname(__file__), 'templates/user.html')
        self.response.out.write(template.render(tmpl, context))   
  
class View_Document(webapp.RequestHandler):
    
    def get(self, name, filename, reply_id=None):
        user = get_user()
        document = get_document(name, filename)
        document.set_view()
        commentary = Commentary(name, filename)

        context = {

            'rating_threshold': 1,
            'commentary': commentary,
            'document': document,
            'filename': filename,
            'subtitle': document.subtitle,
            'name':     name,
            'user':      user,
            'login':     users.create_login_url(self.request.uri),
            'logout':    users.create_logout_url(self.request.uri)
        }
        tmpl = path.join(path.dirname(__file__), 'templates/document.html')
        self.response.out.write(template.render(tmpl, context))          

application = webapp.WSGIApplication([
    ('/tag_browser/',Tag_Browser),
    ('/tag/(.+)/',Tag_Page),
    ('/favorite/',Favorite),
    ('/subscription_handler/', Subscription_Handler),
    ('/invite_handler/', Invite_Handler),
    ('/invite/', Invite),
    ('/availability/', Username_Check),
    ('/update_models/(.*)./', Update_Models),                                      
    ('.*/tag_(.*)/', TagManager),
    ('/admin/', Admin),
    ('.*/reply_box/', ReplyBox),
    ('.*/comment_box/', CommentBox),
    ('.*/rate/', Rating),
    ('.*/comment/', CommentHandler),
    ('/user/(.*)/', UserPage),
    ('/register', Register),
    ('/create', Create_Document),
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
    
