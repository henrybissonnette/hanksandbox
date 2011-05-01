
from google.appengine.dist import use_library
use_library('django', '1.2')

from os import path
from google.appengine.api import mail, memcache, users
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from cgi import escape
import os, re, logging, sys





def get_document(name, filename, title=None):
    #logging.info('in get name/title: /' + name + '/' + title)
    #logging.info('authorname query: ' + str(Document.all().filter('authorname ==',name).fetch(5)))
    #logging.info('title query: ' + str(Document.all().filter('title ==',title).fetch(5)))
    try:
        if filename:
            document = Document.all().filter('authorname ==',name).filter('filename ==',filename)[0]
        else:
            document = Document.all().filter('authorname ==',name).filter('title ==',title)[0]
        return document
    except:
        return None

def get_documents(tag_list=[], tag_not_list=[], type=None):
    """ tag_list should be a string list of tags """
        
    document_query = Document.all()
    if type: 
        document_query.filter("type ==",type)
    for tag in tag_list:
        document_query.filter("tags ==",tag)
    for tag in tag_not_list:
        document_query.filter("tags !=",tag)
    documents = document_query.fetch(1000)
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
        user = User.all().filter('username ==', name).fetch(1)[0]
    else:
        try:
            user = User.all().filter('google ==', users.get_current_user()).fetch(1)[0]
        except:
           return None
    if user == None:
        return None
    if admincheck():
        user.admin = True 
        user.put()
    else:
        user.admin = False 
        user.put()
    return user

def cleaner(value, deletechars = ' `~!@#$%^&*()+={[}]|\"\':;?/>.<,'):
    for c in deletechars:
        value = value.replace(c,'')
    return value;

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
        
        if document_filename:
            self.comments = get_document(username, document_filename).comments.order('-date')
        else:      
            self.comments = get_user(username).mypagecomments.order('-date')
        self.comment_tree = self.prepare_reply_tree(self.comments)
        self.delta =  self.delta_builder(self.comment_tree[1])  
        self.sum_delta = [1] * sum([item for sublist in self.delta for item in sublist])
        self.keys = [str(comment.key()) for comment in self.comment_tree[0]]   
        self.comment_data = zip(self.comment_tree[0], self.keys, self.delta)


class User(db.Model):
    
    google = db.UserProperty()
    username = db.StringProperty()
    reputation = db.IntegerProperty(default=0)
    admin = db.BooleanProperty(default=False)

class Document(db.Model):
    
    author = db.ReferenceProperty(User, collection_name = 'works')
    authorname = db.StringProperty()
    content = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    filename = db.StringProperty()
    title = db.StringProperty()
    subtitle = db.StringProperty(multiline=True)
    rating = db.IntegerProperty(default=0)
    tags = db.StringListProperty(default=[])
    type = db.StringListProperty(default=["not_meta"])
    
    def remove(self):
        replies = self.comments
        for reply in replies:
            reply.remove()
        self.delete()

class Comment(db.Model):
    """It might also be more elegant to 
    manage depth with a property here."""
    author = db.ReferenceProperty(User, collection_name = 'mycomments')
    content = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    above = db.SelfReferenceProperty(collection_name='replies')
    article = db.ReferenceProperty(Document,collection_name='comments')
    user_page = db.ReferenceProperty(User, collection_name='mypagecomments')
    rating = db.IntegerProperty(default=0)
    subject = db.StringProperty()
    
    def remove(self):
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
    
class Tag(db.Model):
    """ Tags should be instantiated with their title as a key_name """
    parent_tag = db.SelfReferenceProperty(collection_name='children')
    title = db.StringProperty()
    ancestors = db.StringListProperty()
    
    def populate_ancestors(self, ancestry = None):
        if not ancestry:
            if self.parent_tag:               
                ancestry = [self.title, self.parent_tag.title]
                return self.populate_ancestors(ancestry)
            else:
                self.ancestors = [self.title]
        else:
            if Tag.get_by_key_name(ancestry[-1]).parent_tag:
                ancestry.append(Tag.get_by_key_name(ancestry[-1]).parent_tag.title)
                return self.populate_ancestors(ancestry)
            else:
                self.ancestors = ancestry
                
    def populate_descendants(self, descendants = None):
        if not descendants:
            descendants = [self.title]
            if self.children:
                for child in self.children:
                    descendants.extend(populate_descendants(child))
                return descendants
            else:
                return descendants
            
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
        
                
            
    
class Admin(webapp.RequestHandler):
    def get(self):
        user = get_user()
        #if not user.admin:
                #self.redirect('/home')
        
        context = {
                   'user':      user,
                   'login':     users.create_login_url(self.request.uri),
                   'logout':    users.create_logout_url(self.request.uri)                       
                   }     
        tmpl = path.join(path.dirname(__file__), 'templates/admin.html')
        self.response.out.write(template.render(tmpl, context))   


class Home(webapp.RequestHandler):
    
    def get(self):
        if self.request.path != '/home':
            self.redirect('/home')
        user = get_user()
        if users.get_current_user():
            if not user:
                self.redirect('/register')
        main_documents = get_documents(type='not_meta')
        meta_documents = get_documents(type='meta')
        context = {
                   'meta_documents': meta_documents,
                   'main_documents': main_documents,
                    'user':      user,
                   'login':     users.create_login_url(self.request.uri),
                   'logout':    users.create_logout_url(self.request.uri)                       
                   }     
        tmpl = path.join(path.dirname(__file__), 'templates/home.html')
        self.response.out.write(template.render(tmpl, context))   


class Register(webapp.RequestHandler):
    
    def get(self):
        user = get_user()
        if user:
            if user.username:
                self.redirect('/home')
        if (not user) and users.get_current_user():
            user = User()
            user.google = users.get_current_user()
            user.put()
        else: 
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
        user.google = users.get_current_user()
        user.username = escape(self.request.get('username'))
        user.put()
        self.redirect('/home')

    

class View_Document(webapp.RequestHandler):
    
    def get(self, name, filename, reply_id=None):
        user = get_user()
        document = get_document(name, filename)
        commentary = Commentary(name, filename)

        context = {
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
        existing_filename = self.request.get('existing_filename')
        filename = self.request.get('filename')
        filename = cleaner(filename)
        username = self.request.get('username')
        
        # username only gets passed on an edit
        if username:
            document = get_document(username,existing_filename)
        else:
            # if new document uses existing filename this will happen
            if get_document(user.username,filename):
                document = get_document(user.username,filename)
            else:
                document = Document()
            
        tags_pre_pre = self.request.get_all('added_tag')
        #create ancestors for pre ancestor tags (soon to be uneccessary)
        
        for tag in tags_pre_pre:
            update = Tag.get_by_key_name(tag)
            update.populate_ancestors()
            update.put()
            
        tags_pre = [Tag.get_by_key_name(title).ancestors for title in tags_pre_pre]
        tags = [item for sublist in tags_pre for item in sublist]
        tags = remove_duplicates(tags)
        if 'Meta' in tags:
            if 'meta' not in document.type:
                try:
                    document.type.remove('not_meta')
                except:
                    pass
                document.type.append('meta')
        document.tags = tags
        
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
        document.put()
         
        mail.send_mail(
            user.google and user.google.email() or 'postmaster@hanksandbox.appspotmail.com',
            'hankster81@yahoo.com',
            'Comment from %s' % document.authorname,
            '%s wrote: \r\n\r\n"%s"' % (document.authorname, document.content),
        )

        self.redirect('/' + document.authorname + '/document/'+  filename + '/')
        
class Edit_Document(webapp.RequestHandler):
    def get(self,name,filename):
        user = get_user()
        userdocuments = user.works
        document = get_document(name, filename)
        added_tags = [Tag.get_by_key_name(title) for title in  document.tags]
        context = {
                   'userdocuments':userdocuments,
                   'added_tags':added_tags,
                   'document':  document,
                   'user':      user,
                   'login':     users.create_login_url(self.request.uri),
                   'logout':    users.create_logout_url(self.request.uri)
                   }     
        tmpl = path.join(path.dirname(__file__), 'templates/create.html')
        self.response.out.write(template.render(tmpl, context))
        
class Delete_Document(webapp.RequestHandler):
    def get(self,name,filename):
        document = get_document(name,filename)
        document.remove()
        self.redirect('/user/' + name + '/')
        
        
        

class CommentHandler(webapp.RequestHandler):
    def post(self):
        comment_type = self.request.get('comment_type')
        
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
            if user:
                if user.username:
                    comment.author = user
                    commenter = user.username
            else:
                commenter = 'anonymous'
                
            comment.content = self.request.get('content')
            comment.put()
            
            mail.send_mail(
                'postmaster@hanksandbox.appspotmail.com',
                'hankster81@yahoo.com',
                'Comment from %s' % commenter,
                '%s wrote: \r\n\r\n"%s"' % (commenter, comment.content),
            )
            self.redirect('..')
      

        
class UserPage(webapp.RequestHandler):
    def get(self, page_user):
        creator = User.all().filter('username ==', page_user).fetch(1)[0]
        user = get_user()
        essays = creator.works
        commentary = Commentary(page_user)
        context = {
                   'commentary':commentary,
                   'essays':    essays,
                   'page_user': page_user,
                   'user':      user,
                   'login':     users.create_login_url(self.request.uri),
                   'logout':    users.create_logout_url(self.request.uri)
                   }     
        tmpl = path.join(path.dirname(__file__), 'templates/user.html')
        self.response.out.write(template.render(tmpl, context))   
        
class Rating(webapp.RequestHandler):
    
    def post(self):
        user = get_user()
        rating = self.request.get('rating')
        key = self.request.get('key')
        username = self.request.get('username')
        filename = self.request.get('filename')
        logging.info('username: ' + username)
        logging.info('filename: ' + filename)
        if key:
            object = Comment.get(db.Key(key))
        else:
            object = get_document(username,filename)
        if rating == "up":
            rated = 1
            object.rating = object.rating + 1
        else:
            rated = 0
            object.rating = object.rating - 1
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
        
class TagManager(webapp.RequestHandler):
    def post(self, request):
        user = get_user()
        #if not user.admin:
            #self.redirect('/home')
            
        if request == 'create':
            create_title = cleaner(self.request.get('new_title').replace(' ','_'))
            parent_title = self.request.get('parent_title')
            logging.info('create_title: ' + create_title)
            logging.info('parent_title: ' + parent_title)
            tag = Tag(key_name=create_title)
            tag.title = create_title
            if parent_title:
                tag.parent_tag = Tag.get_by_key_name(parent_title)
            tag.populate_ancestors()
            tag.put() 
                
            self.redirect('..')
                
            #parent_tag = Tag.get_by_key_name(parent_title)
            #sister_tags = parent_tag.children
            #context = {
            #    'tags':     sister_tags,
            #    'title':    create_title,
            #   }  
            #tmpl = path.join(path.dirname(__file__), 'templates/tag_request/expand.html')
            #self.response.out.write(template.render(tmpl, context))
            
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
            tag = Tag.get_by_key_name(expand_title)
            tags = tag.children.order('title')
            context = {
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
            logging.info('added_tags: '+ str(added_tags_pre))
            added_tags = [Tag.get_by_key_name(title) for title in  eval(added_tags_pre)]
            context = {'added_tags':added_tags}
            tmpl = path.join(path.dirname(__file__), 'templates/tag_request/addto.html')
            self.response.out.write(template.render(tmpl, context))  
            
        if request == 'base':
            user_type = self.request.get('user_type')
            root_tags = Tag.all().filter('parent_tag ==', None).fetch(100)
            context = {
                       'user_type':user_type,
                       'tags': root_tags,
                       }
            tmpl = path.join(path.dirname(__file__), 'templates/tag_request/base.html')
            self.response.out.write(template.render(tmpl, context))
                  
        if request == 'remove':
            removed = self.request.get('title')
            logging.info('removed: ' + removed)
            Tag.get_by_key_name(removed).exterminate()
            
            context = {}
            tmpl = path.join(path.dirname(__file__), 'templates/tag_request/empty.html')
            self.response.out.write(template.render(tmpl, context))
            
class Update_Models(webapp.RequestHandler):
    def post(self, request):
        adminboot()
        if request == 'start':
            context = {}
            tmpl = path.join(path.dirname(__file__), 'templates/update_models.html')
            self.response.out.write(template.render(tmpl, context))
            
        
            

application = webapp.WSGIApplication([
                                      
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
    
