'''
Created on Apr 29, 2009

@author: rowhite
'''

import urllib
import urlparse
import logging

import methods
import request
import response
from error import *

class PbLogHandler(logging.Handler):
    def emit(self, record):
        pass

h = PbLogHandler()
logging.getLogger('pb').addHandler(h)

class PbApi(object):
    '''
    Main class for photobucket API interaction
    pb_request -- PbRequest
    response -- PbResponse
    methods -- PbMethod current method engine
    method_stack -- fluent call stack
    params -- api key value pairs
    __uri -- current uri
    username -- current username
    no_reset -- flag to not reset after method call to server
    '''
    pb_request = None
    response = None
    response_string = ''
    __methods = None
    method_stack = []
    params = {}
    __uri = ''
    username = ''
    no_reset = False
    __validation_map = None
    __logger = logging.getLogger('pb')

    def __init__(self, consumer_key, consumer_secret, subdomain='api',
                 default_format='xml'):
        '''
        Constructor
        @param consumer_key: str
        @param consumer_secret: str
        @param subdomain: str photobucket api subdomain
        @param default_format: str xml or json
        '''
        self._load_method_class('base')
        self.pb_request = request.PbRequest(subdomain, default_format)
        self.pb_request.set_oauth_consumer(consumer_key, consumer_secret)
        
    def _load_method_class(self, method_name):
        '''Load a method class
        @param method_name: name of method
        @raise AttributeError: if invalid method is called
        '''
        method_class = getattr(methods, method_name.capitalize())(self)
        return self._set_methods(method_class)
    
    def _set_methods(self, method):
        '''set the current method class
        @param method: PbMethod
        '''
        self.__methods = method
        return self
    methods = property(lambda self: self.__methods, None)
    
    def set_oauth_token(self, token, token_secret, username=None):
        self.pb_request.set_oauth_token(token, token_secret)
        if username: self.username = username
        return self
    oauth_token = property(lambda self: self.pb_request.oauth_token, None)
    
    def set_subdomain(self, subdomain):
        self.pb_request.set_subdomain(subdomain)
        return self
    subdomain = property(lambda self: self.pb_request.subdomain, set_subdomain)
    
    def set_response_parser(self, type):
        '''
        Set the response parser
        @param type: str name of parser
                     One of classes in pbapi.response
        @raise AttributeError: if invalid parser name is called
        '''
        self.response = getattr(response, type.capitalize())()
        self.pb_request.default_format = self.response.format
        return self
    
    def reset(self, uri=True, methods=True, params=True, auth=False):
        '''
        reset current api client data state
        @param uri: bool reset uri data
        @param methods: bool reset method data (current method depth/stack)
        @param params: bool reset all parameters
        @param auth: bool reset auth token
        '''
        if uri: self.__uri = None
        if methods:
            self.methods._reset()
            self.method_stack = []
        if params: self.params = {}
        if auth: self.pb_request.oauth_token = None
        return self
    
    def __get_base_string(self):
        return self.pb_request.base_string
    base_string = property(__get_base_string, None)
    
    def get_parsed_response(self, onlycontent=False):
        if not self.response:
            raise PbApiError(message="No parser set up", core=self)
        try:
            return self.response.parse(self.response_string.strip(), onlycontent)
        except PbApiErrorResponse, err:
            err.core = self
            raise err
    parsed_response = property(get_parsed_response, None)
    
    def __get_login_url(self):
        return self.pb_request.get_login_url()
    login_url = property(__get_login_url, None)
    
    def get(self):
        '''
        Forward a GET to the server based upon the current uri & param state
        '''
        self.__validate_request('get')
        self.response_string = self.pb_request.get(self.uri, self.params)
        if not self.no_reset: self.reset()
        return self
    
    def post(self):
        '''
        Forward a POST to the server based upon the current uri & param state
        '''
        self.__validate_request('post')
        self.response_string = self.pb_request.post(self.uri, self.params)
        if not self.no_reset: self.reset()
        return self
    
    def put(self):
        '''
        Forward a PUT to the server based upon the current uri & param state
        '''
        self.__validate_request('put')
        self.response_string = self.pb_request.put(self.uri, self.params)
        if not self.no_reset: self.reset()
        return self
    
    def delete(self):
        '''
        Forward a DELETE to the server based upon the current uri & param state
        '''
        self.__validate_request('delete')
        self.response_string = self.pb_request.delete(self.uri, self.params)
        if not self.no_reset: self.reset()
        return self
    
    def load_token_from_response(self, subdomain=True):
        '''
        Load and set the current OAuth token from the last response string
        @param subdomain: bool true if you want to also set the current sub
        @return: PbApi
        '''
        string = self.response_string.strip()
        try:
            from urlparse import parse_qs
        except ImportError:
            from cgi import parse_qs
        params = parse_qs(string)
        try:
            self.set_oauth_token(params['oauth_token'][0],
                                 params['oauth_token_secret'][0],
                                 params.get('username', [''])[0])
            if subdomain and params.get('subdomain', '') != '':
                self.subdomain = params['subdomain'][0]
            return self
        except KeyError:
            raise PbApiError(core=self,
                             message="Token and Token Secret not in response")
    
    def _set_uri(self, uri, replacements=None):
        '''
        Set the current URI
        @param uri: str sprtintf format
        @param replacements: list if uri has %s replacements this list will be 
                             urllib.quoted and inserted
        @return: self
        '''
        if replacements is not None:
            if isinstance(replacements, basestring):
                replacements = urllib.quote(replacements, '~')
            else:
                replacements = tuple(map(lambda x: urllib.quote(x, '~'),
                                         replacements))
            self.__uri = uri % replacements
        else:
            self.__uri = uri
        return self
    
    def _append_uri(self, uri, replacements=None):
        '''
        append more to the current uri
        @param uri: str sprtintf format
        @param replacements: list if uri has %s replacements this list will be 
                             urllib.quoted and inserted
        @return: self
        '''
        if replacements is not None:
            if isinstance(replacements, basestring):
                replacements = urllib.quote(replacements, '~')
            else:
                replacements = tuple(map(lambda x: urllib.quote(x, '~'),
                                         replacements))
            self.__uri += uri % replacements
        else:
            self.__uri += uri
        return self
    uri = property(lambda self: self.__uri, None)
    
    def __validate_request(self, method):
        '''
        Validate the request
        @param method: str http method to check
        @raise PbApiError: If method is invalid or missing parameters
        '''
        # get validation map
        valmap = self._load_method_validation_map()
        if not valmap: return True
        # fixup stack
        stack = self.method_stack
        if len(stack) < 2:
            stack.append('_default')
        try:
            valid_params = valmap[stack[0]][stack[1]][method]
            if valid_params:
                unknowns = [param for param in self.params.keys()\
                        if not valid_params.has_key(param)]
                missing = dict([(param, valid_params[param])\
                                for param in valid_params.keys()\
                                if not self.params.has_key(param)])
            else: 
                unknowns = self.params
                missing = {}
            
            if unknowns:
                self.__logger.warn("Unknown parameters: %s" % ', '.join(unknowns))
            for key, val in missing.items():
                if val != 'required':
                    missing.pop(key)
                elif key == 'aid' or key == 'mid' or\
                     key == 'uid' or key == 'tagid':
                    missing.pop(key)
            if missing:
                msg = "missing required parameters: %s" % ', '.join(missing.keys())
                raise PbApiError(message=msg, core=self)
        except KeyError:
            raise PbApiError(message="invalid method %s" % method,
                             core=self)
        
        return self
    
    def _load_method_validation_map(self):
        if self.__validation_map is None:
            try:
                import yaml
                import os.path
                path = os.path.dirname(__file__) + '/data/api-defs.yml'
                self.__validation_map = yaml.load(open(path))
            except ImportError, IOError:
                #yaml unavailable or file not found
                self.__validation_map = False
        return self.__validation_map
    
    def __getattr__(self, name):
        '''
        default method to forward any undefined calls to method class
        @param name: method name
        '''
        # there's gotta be a better way to get the method ref by name
        try:
            method = getattr(self.methods, name)
            self.method_stack.append(name)
        except AttributeError:
            raise PbApiError(message="Invalid method call: %s" % name, core=self)
        def call_it(*args, **kwargs):
            return method(*args, **kwargs)
        return call_it
