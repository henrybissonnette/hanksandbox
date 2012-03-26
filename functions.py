from BeautifulSoup import BeautifulSoup
import logging

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

def parse(text, elements=[], attributes=[], styles=[]):
    counter = 0
    contentTemp = text 
    while True:
        counter += 1
        soup = BeautifulSoup(contentTemp)
        removed = False        
        for tag in soup.findAll(True): # find all tags
            if tag.name not in elements:
                if tag.contents:
                    tag.replaceWith(tag.contents[0])
                else:
                    tag.extract()
                removed = True
            else: # it might have bad attributes               
                for attr in tag._getAttrMap().keys():
                    if attr not in attributes:
                        del(tag[attr])
                        removed = True
                    else:
                        if styles:
                            if attr == 'style' and not tag[attr] in styles:
                                del(tag[attr])   
                                removed = True                  
    
        # turn it back to html
        fragment = unicode(soup)
        if removed:
            # tricks can exploit a single pass
            # we need to reparse the html until it stops changing
            contentTemp = fragment
            continue # next round           
        break   
    return contentTemp

def resolve(obj, path):
    """Resolves an attribute path on an object, returning `None` 
       if any attribute is not found"""
    for name in path.split("."):
        obj = getattr(obj, name, None)
        if obj is None:
            break
    return obj

def cleaner(value, deleteChars = ' `~!@#$%^&*()+={[}]|\"\':\\;?/>.<,', replaceChars=[]):
    value = parse(value)
    for char, replacement in replaceChars:
        value = value.replace(char,replacement)
    for c in deleteChars:
        value = value.replace(c,'')
    return value;

