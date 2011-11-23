from functions import get_user
from google.appengine.ext import db
from google.appengine.api import memcache, users
from google.appengine.ext import webapp

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
    
    minimizeThreshold = db.IntegerProperty(default=3)
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
            self.set_subscription([],username) 
            affected.append(other)      
            
        for comment in self.mycomments:
            #potential ERROR if some comments are descendants of others
            comment.remove()
            
        for document in self.works:
            document.remove()
            
        for message in self.streamMessages:
            message.remove()
            
        for rating in self.ratings:
            rating.delete()
            
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
            
        if reputation < 0:
            reputation = -(math.sqrt(math.fabs(reputation))/100)*97
        else:
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
        
    def set_subscription(self, subscriptions, subscribee):
        """ SUBSCRIPTIONS is a list of values one each for email and stream 
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
        rating = 40
        tally = 10
        for vote in votes:
            if vote == -1:
                tenBase = 0
            else: 
                tenBase = 10
            rating = rating + tenBase*(vote.user.reputation)
            tally = tally + vote.user.reputation           
        rating = rating/tally
        logging.info('rating = '+str(rating))
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
            return Document.all().filter("draft ==",False).order('-date').fetch(1000)
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
    type = db.StringProperty(default = 'comment')     
        

