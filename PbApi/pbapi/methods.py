'''
Created on Apr 29, 2009

@author: rowhite
'''

import pbapi
from error import *

class PbMethods(object):
    '''
    Parent class for api access methods
    core -- PbApi core class
    '''
    core = None


    def __init__(self, core):
        '''
        Constructor
        @param core: PbApi core class
        '''
        self.core = core
    
    def _reset(self):
        self._load('base')
    
    def _load(self, method_name):
        return self.core._load_method_class(method_name)

class Base(PbMethods):
    '''
    Base API Methods class
    '''
    
    def ping(self, params={}, *args, **kwargs):
        '''
        ping
        @param params: dict api params
        '''
        if params:
            self.core.params = params
        self.core._set_uri('/ping')
        return self.core
    
    def search(self, term, params={}, *args, **kwargs):
        '''
        search
        @param term: str search term, '-' for recent
        @param params: dict api params
        '''
        if not term: term = '-'
        self.core._set_uri('/search/%s', term)
        self.core.params = params
        self._load('search')
        return self.core
    
    def featured(self, *args, **kwargs):
        '''
        featured
        '''
        self.core._set_uri('/featured')
        self._load('featured')
        return self.core
    
    def user(self, username='', params={}, *args, **kwargs):
        '''
        User
        @param username: str username, [optional, default current user token]
        @param params: dict api params
        '''
        if isinstance(username, dict) and not params:
            params = username
            username = ''
        self.core._set_uri('/user/%s', username)
        self.core.params = params
        self._load('user')
        return self.core
    
    def album(self, albumpath, params={}, *args, **kwargs):
        '''
        User Album
        @param albumpath: str album path (username/location)
        @param params: dict api params
        '''
        if not albumpath:
            raise PbApiError(message="albumpath required", core=self.core)
        self.core._set_uri('/album/%s', albumpath)
        self.core.params = params
        self._load('album')
        return self.core
    
    def group(self, group, params={}, *args, **kwargs):
        '''
        Group Album
        @param group: str group hash
        @param params: dict api params
        '''
        if not group:
            raise PbApiError(message="group required", core=self.core)
        self.core._set_uri('/group/%s', group)
        self.core.params = params
        self._load('group')
        return self.core
    
    def media(self, mediaurl, params={}, *args, **kwargs):
        '''
        Media
        @param mediaurl: str media url 
           (http://i338.photobucket.com/albums/v000/username/location/filename.gif)
        @param params: dict api params
        '''
        if not mediaurl:
            raise PbApiError(message="mediaurl required", core=self.core)
        self.core._set_uri('/media/%s', mediaurl)
        self.core.params = params
        self._load('media')
        return self.core
    
    def login(self, params={}, *args, **kwargs):
        '''
        Login
        @param params: dict api params
        '''
        self.core._set_uri('/login')
        self.core.params = params
        self._load('login')
        return self.core
    
    def accessor(self, params={}, *args, **kwargs):
        '''
        get accessor tokens
        @param params: dict api params
        '''
        self.core._set_uri('/accessor')
        self.core.params = params
        return self.core

class Search(PbMethods):
    '''
    Search API methods class
    '''
    def image(self, params={}, *args, **kwargs):
        '''
        search for images
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/image')
        return self.core
    
    def video(self, params={}, *args, **kwargs):
        '''
        search for videos
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/video')
        return self.core
    
    def group(self, params={}, *args, **kwargs):
        '''
        search for groups
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/group')
        return self.core
    
    def subscribe(self, subid='', params={}, *args, **kwargs):
        '''
        subscribe to term
        @param params: dict api params
        '''
        if isinstance(subid, dict) and not params:
            params = subid
            subid = ''
        self.core.params = params
        self.core._append_uri('/subscribe/%s', params)
        return self.core
    
class Featured(PbMethods):
    '''
    Featured api methods class
    '''
    def homepage(self, params={}, *args, **kwargs):
        '''
        get the homepage features
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/homepage')
        return self.core
    
    def group(self, params={}, *args, **kwargs):
        '''
        get the feature groups
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/group')
        return self.core
    
class User(PbMethods):
    '''
    User api methods class
    '''
    def search(self, params={}, *args, **kwargs):
        '''
        search
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/search')
        return self.core
    
    def url(self, params={}, *args, **kwargs):
        '''
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/url')
        return self.core
    
    def contact(self, params={}, *args, **kwargs):
        '''
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/contact')
        return self.core
    
    def group(self, params={}, *args, **kwargs):
        '''
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/group')
        return self.core
    
    def uploadoption(self, params={}, *args, **kwargs):
        '''
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/uploadoption')
        return self.core
    
    def tag(self, tagname='', params={}, *args, **kwargs):
        '''
        @param tagname: str name of a single tag to get media for
        @param params: dict api params
        '''
        if isinstance(tagname, dict) and not params:
            params = tagname
            tagname = ''
        self.core.params = params
        self.core._append_uri('/tag/%s', tagname)
        return self.core
    
    def subscription(self, subid='', params={}, *args, **kwargs):
        '''
        @param subid: int id of a single subscription
        @param params: dict api params
        '''
        if isinstance(subid, dict) and not params:
            params = subid
            subid = ''
        self.core.params = params
        self.core._append_uri('/subscription/%s', subid)
        return self.core
    
class AlbumBase(PbMethods):
    '''
    Album Parent API Methods class
    '''
    def upload(self, params={}, *args, **kwargs):
        '''
        upload a file
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/upload')
        return self.core
    
    def privacy(self, params={}, *args, **kwargs):
        '''
        privacy
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/privacy')
        return self.core
    
    def vanity(self, params={}, *args, **kwargs):
        '''
        vanity
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/vanity')
        return self.core
    
    def subscribe(self, subid='', params={}, *args, **kwargs):
        '''
        subscribe
        @param subid: str subscription id
        @param params: dict api params
        '''
        if isinstance(subid, dict) and not params:
            params = subid
            subid = ''
        self.core.params = params
        self.core._append_uri('/subscribe/%s', subid)
        return self.core
    
    def theme(self, params={}, *args, **kwargs):
        '''
        theme
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/theme')
        return self.core
    
    def url(self, params={}, *args, **kwargs):
        '''
        url
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/url')
        return self.core
    
class Album(AlbumBase):
    '''
    User album api class
    '''
    def organize(self, params={}, *args, **kwargs):
        '''
        organize
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/organize')
        return self.core
    
class Group(AlbumBase):
    '''
    Group album api class
    '''
    def info(self, params={}, *args, **kwargs):
        '''
        info
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/info')
        return self.core
    
    def contributor(self, username='', params={}, *args, **kwargs):
        '''
        contributors
        @param username: str contributor name
        @param params: dict api params
        '''
        if isinstance(username, dict) and not params:
            params = username
            username = ''
        self.core.params = params
        self.core._append_uri('/contributor/%s', username)
        return self.core
    
    def tag(self, tagname='', params={}, *args, **kwargs):
        '''
        @param tagname: str name of a single tag to get media for
        @param params: dict api params
        '''
        if isinstance(tagname, dict) and not params:
            params = tagname
            tagname = ''
        self.core.params = params
        self.core._append_uri('/tag/%s', tagname)
        return self.core
    

class Media(PbMethods):
    '''
    Media api class
    '''
    def description(self, params={}, *args, **kwargs):
        '''
        description
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/description')
        return self.core
    
    def title(self, params={}, *args, **kwargs):
        '''
        title
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/title')
        return self.core
    
    def tag(self, tagid='', params={}, *args, **kwargs):
        '''
        @param tagid: str optional '' for all tags
        @param params: dict api params
        '''
        if isinstance(tagid, dict) and not params:
            params = tagid
            tagid = ''
        self.core.params = params
        self.core._append_uri('/tag/%s', tagid)
        return self.core
    
    def resize(self, params={}, *args, **kwargs):
        '''
        resize
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/resize')
        return self.core
    
    def rotate(self, params={}, *args, **kwargs):
        '''
        rotate
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/rotate')
        return self.core
    
    def meta(self, params={}, *args, **kwargs):
        '''
        meta
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/meta')
        return self.core
    
    def links(self, params={}, *args, **kwargs):
        '''
        links
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/links')
        return self.core
    
    def related(self, params={}, *args, **kwargs):
        '''
        related
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/related')
        return self.core
    
    def share(self, params={}, *args, **kwargs):
        '''
        share
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/share')
        return self.core
    
    def comment(self, params={}, *args, **kwargs):
        '''
        comment
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/comment')
        return self.core
    
    def rating(self, params={}, *args, **kwargs):
        '''
        rating
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/rating')
        return self.core
    
class Login(PbMethods):
    '''
    login api class
    '''
    def request(self, params={}, *args, **kwargs):
        '''
        request
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/request')
        return self.core
    
    def access(self, params={}, *args, **kwargs):
        '''
        access
        @param params: dict api params
        '''
        self.core.params = params
        self.core._append_uri('/access')
        return self.core
    