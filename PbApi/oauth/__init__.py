'''
Created on Apr 27, 2009

@author: rowhite
'''
import urllib
import random
import time
from urlparse import urlparse
from cgi import parse_qs

import utils
import signature

class OAuthToken(object):
    """
    OAuth Token representation
    """
    key = None
    secret = None
    
    def __init__(self, key, secret):
        '''
        Create a token
        @param key: str
        @param secret: str
        '''
        self.key = key
        self.secret = secret
        
    def __str__(self):
        return urllib.urlencode({'oauth_token': self.key,
                                 'oauth_token_secret': self.secret})

class OAuthConsumer(object):
    '''
    OAuth Consumer representation
    '''
    key = None
    secret = None
    
    def __init__(self, key, secret):
        '''
        Create a Consumer
        @param key: str
        @param secret: str
        '''
        self.key = key
        self.secret = secret
    
    def __str__(self):
        return quote_plus(self.key)

class OAuthRequest(object):
    '''
    OAuth Request representation
    '''
    parameters = {}
    http_method = ''
    http_url = ''
    base_string = ''
    key_string = ''
    version = '1.0'
    
    def __init__(self, http_method, http_url, parameters=None):
        '''
        Request Constructor
        @param http_method: str http method
        @param http_url: str url
        @param parameters: dict key-value params
        '''
        self.parameters = parameters or {}
        self.http_method = http_method.upper()
        self.http_url = http_url
    
    @staticmethod
    def from_request(http_method, http_url, parameters=None, headers=None,
                     query_string=None):
        '''
        @param http_method: str
        @param http_url: str
        @param parameters: dict
        @param headers: str
        '''
        if parameters:
            return OAuthRequest(http_method, http_url, parameters)
        # build parameters from qs and headers
        parameters = {}
        if headers and 'Authorization' in headers:
            parameters.update(OAuthRequest.split_header(headers['Authorization']))
        if query_string:
            parameters.update(OAuthRequest.split_qs(query_string))
        return OAuthRequest(http_method, http_url, parameters)
    
    @staticmethod
    def from_url(url, http_method='GET', consumer=None, token=None):
        '''
        Build up a request from url and consumer
        @param url: str http url
        @param http_method: str
        @param consumer: OAuthConsumer
        @param token: OAuthToken
        '''
        parts = urlparse(url)
        parameters = parse_qs(parts.query)
        if consumer:
            return OAuthRequest.from_consumer_and_token(consumer, token, 
                                                        http_method, url, 
                                                        parameters)
        else:
            raise NotImplementedError
    
    @staticmethod
    def from_consumer_and_token(consumer, token, http_method, http_url, 
                                parameters={}):
        '''
        Create request from consumer and token as well (for a new request)
        @param consumer: OAuthConsumer
        @param token: OAuthToken
        @param http_method: str
        @param http_url: str
        @param parameters: dict
        '''
        defaults = {'oauth_version': OAuthRequest.version,
                    'oauth_nonce': OAuthRequest.get_nonce(),
                    'oauth_timestamp': OAuthRequest.get_timestamp(),
                    'oauth_consumer_key': consumer.key}
        defaults.update(parameters)
        if token:
            defaults['oauth_token'] = token.key
        return OAuthRequest(http_method, http_url, defaults)
    
    def set_parameter(self, name, value):
        self.parameters[name] = value
    
    def get_parameter(self, name):
        try:
            return self.parameters[name]
        except KeyError:
            return None
    
    @staticmethod
    def get_normalized_http_url(url):
        parts = urlparse(url)
        port = ''
        if parts.port and parts.port != 80:
            port = ':%s' % parts.port
        return ''.join([parts.scheme, '://', parts.hostname, port, '/',
                        parts.path.strip('/')])
    
    def to_url(self):
        return '?'.join([self.http_url, self.to_post_data()])
    
    def to_post_data(self):
        return utils.normalize_parameters(self.parameters)
    
    def to_header(self):
        return ','.join(['Authorization: OAuth realm=""',
                         utils.normalize_parameters(self.parameters, ',')])
    
    def __str__(self):
        return self.to_url()

    def sign_request(self, signature_method, consumer, token=None):
        '''
        Signs this request - adds params for signature method and the signature
        @param signature_method: str signing method identifier
        @param consumer: OAuthConsumer consumer to sign against
        @param token: OAuthToken to sign against
        '''
        method = signature.get_signature_method(signature_method)
        self.set_parameter('oauth_signature_method', method.get_method_name())
        token_secret = token and token.secret or ''
        
        sig = method.sign_request(self, consumer.secret, token_secret)
        self.set_parameter('oauth_signature', sig)
        
    
    @staticmethod
    def get_timestamp():
        return int(time.time())

    @staticmethod
    def get_nonce():
        ''' get a psuedo random string '''
        random_str = str(random.random())
        try:
            import hashlib
            return hashlib.md5(random_str).hexdigest()
        except ImportError:
            import md5
            return md5.new(random_str).hexdigest()
    
    @staticmethod
    def split_header(header):
        parts = header.split(',')
        params = {}
        for param in parts:
            param = param.strip()
            if not param.startswith('oauth'): continue
            
            param_parts = param.split('=')
            params[utils.urldecode_rfc3986(param_parts[0])] = \
                    utils.urldecode_rfc3986(param_parts[1].strip('"'))
            
        return params

    @staticmethod
    def split_qs(qs):
        '''
        split a qs into parameters for OAuth
        @param qs: str postdata or url qs
        '''
        params = parse_qs(qs, True)
        parameters = {}
        for key, val in params.iteritems():
            parameters[key] = [urllib.unquote(v) for v in val]
        return parameters