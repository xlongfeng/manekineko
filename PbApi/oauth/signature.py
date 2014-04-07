'''
Created on Apr 11, 2009

@author: rowhite
'''

from utils import *
import hmac
import binascii


def normalize_hash_method(method):
    return method.replace(' ', '_').replace('-', '_').lower()


def get_signature_method(method):
    '''
    @rtype: OAuthSignature
    @raise KeyError: If the signature is not a valid type for this OAuth lib
                    Valid types are hmac_sha1 and plaintext
    '''
    signature_types = {'hmac_sha1': OAuthSignature_hmac_sha1,
                       'plaintext': OAuthSignature_plaintext}
    name = normalize_hash_method(method)
    return signature_types[name]()


def build_signature(method, 
                    request, 
                    consumer_secret, 
                    token_secret=None):
    return get_signature_method(method).sign_request(request, 
                                                     consumer_secret, 
                                                     token_secret)


class OAuthSignature(object):
    '''
    Abstract definition of an OAuth signature method
    '''

    def sign_request(self, 
                     request, 
                     consumer_secret, 
                     token_secret=None):
        '''
        Sign a request using this signature method
        @param request: OAuthRequest
        @param consumer_secret: str consumer secret key
        @param token_secret: str token secret key
        @rtype: str
        '''
        raise NotImplementedError
    
    def get_method_name(self):
        '''
        Get the OAuth official string representation for this method
        @rtype: str
        '''
        raise NotImplementedError
    
    def generate_key_string(self, consumer_secret, token_secret=''):
        return '&'.join([urlencode_rfc3986_utf8(consumer_secret), \
                         urlencode_rfc3986_utf8(token_secret)])


class OAuthSignature_hmac_sha1(OAuthSignature):
    '''
    OAuth HMAC-SHA1 Implementation
    '''
    OAUTH_SIGNATURE_METHOD = 'HMAC-SHA1'
    
    def get_method_name(self):
        return self.OAUTH_SIGNATURE_METHOD
    
    def sign_request(self, request, consumer_secret, token_secret=''):
        '''
        Sign a request
        @param request: OAuthRequest request to sign
        @param consumer_secret: str consumer secret to sign with
        @param token_secret: str Authentication secret to sign with
        '''
        base_string = self.generate_base_string(request.http_method, 
                                                request.http_url, 
                                                normalize_parameters(get_filtered_base_string_params(request.parameters)))
        # for debug
        request.base_string = base_string
        
        key = self.generate_key_string(consumer_secret, token_secret)
        # for debug
        request.key_string = key
        
        return self.calculate_hash(base_string, key)
    
    def generate_base_string(self, http_method, uri, param_string):
        '''
        Creates the basestring needed for signing per oAuth SEction 9.1.2
        @param http_method: str one of the http methods GET, POST, etc.
        @param uri: str the uri; the url without the querystring
        @param param_string: str normalized parameters
        @return: str concatenation fot he encoded parts of the basestring
        '''
        return '&'.join([urlencode_rfc3986(http_method), \
                         urlencode_rfc3986(uri), \
                         urlencode_rfc3986_utf8(param_string)])
    
    def calculate_hash(self, basestring, key):
        '''
        Calculates the hmac-sha1 secret
        
        @param basestring: str basestring from generate_base_string
        @param key: str key to hash against
        @return: str base64 encoded signature
        '''
        try:
            import hashlib
            digestmod = hashlib.sha1
        except ImportError:
            import sha
            digestmod = sha
        hasher = hmac.new(key, basestring, digestmod)
        return binascii.b2a_base64(hasher.digest())[:-1]
    
    
class OAuthSignature_plaintext(OAuthSignature):
    '''
    OAuth PLAINTEXT Implementation
    '''
    OAUTH_SIGNATURE_METHOD = 'PLAINTEXT'
    
    def sign_request(self, request, consumer_secret, token_secret=''):
        '''
        Sign a request
        @param request: OAuthRequest request to sign
        @param consumer_secret: str consumer secret to sign with
        @param token_secret: str Authentication secret to sign with
        '''
        # for debug
        request.base_string = ''
        
        key = self.generate_key_string(consumer_secret, token_secret)
        # for debug
        request.key_string = key
        
        return urlencode_rfc3986_utf8(key)
    
    def get_method_name(self):
        return self.OAUTH_SIGNATURE_METHOD
    
    