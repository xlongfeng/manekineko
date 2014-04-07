'''
Created on Apr 29, 2009

@author: rowhite
'''
import re
import os.path
import mimetypes, mimetools
from cStringIO import StringIO
import logging

import httplib2

from oauth import *
from error import *

class PbRequest(object):
    '''
    Pb Api Request class
    Tackles makeing http calls
    Handles photobucket subdomain base string issues with oauth
    '''
    __oauth_consumer = None
    oauth_token = None
    __subdomain = None
    __logger = logging.getLogger('pb')
    default_format = None
    request_url = None
    oauth_request = None
    __http2 = None
    __response_headers = None
    __web_login_url = 'http://photobucket.com/apilogin/login'
    __redirect_depth = 0
    __MAX_REDIRECTS = 3
    __current_redirect = 0


    def __init__(self, subdomain='api', default_format='xml'):
        '''
        Constructor
        @param subdomain: str photobucket api subdomain
        @param default_format: str default xml
        '''
        self.default_format = default_format
        self.subdomain = subdomain
    
    def set_subdomain(self, subdomain):
        subdomain = re.sub('\.photobucket\.com(/.*)?', '', 
                           subdomain).replace('http://','')
        self.__subdomain = subdomain
    subdomain = property(lambda self: self.__subdomain, set_subdomain)
    
    response_headers = property(lambda self: self.__response_headers, None)

    def set_oauth_consumer(self, consumer_key, consumer_secret):
        '''
        Set the oauth consumer
        @param consumer_key: str
        @param consumer_secret: str
        '''
        self.__oauth_consumer = OAuthConsumer(consumer_key, consumer_secret)

    def set_oauth_token(self, token, token_secret):
        '''
        Set the oauth token
        @param token: str token
        @param token_secret: str token secret
        '''
        self.oauth_token = OAuthToken(token, token_secret)
    
    def get_subdomain_url(self, uri=''):
        '''
        get whole subdomain url
        @param uri: str uri ending
        @return: str full url appropriate for this subdomain
        '''
        return ''.join(['http://', self.__subdomain, '.photobucket.com/',
                        uri.strip('/')]).strip('/')
    
    def __get_signed_oauth_request(self, method, uri, params={}):
        req = OAuthRequest.from_consumer_and_token(self.__oauth_consumer,
                                                   self.oauth_token,
                                                   method,
                                                   'http://api.photobucket.com/' + \
                                                   uri.strip('/'),
                                                   params)
        req.sign_request('HMAC-SHA1', self.__oauth_consumer, self.oauth_token)
        return req
    
    def __pre_request(self, method, uri, params):
        '''
        pre-request filter
        signs and configures url appropriately
        @param method: str GET|POST|PUT|DELETE
        @param uri: str path portion of url
        @param params: dict key value params
        @return: str finished request url
        '''
        #cleanup method
        method = method.upper()
        #cleanup/set format
        if self.default_format and 'format' not in params:
            params['format'] = self.default_format
        #remove upload file from parameters
        if 'uploadfile' in params:
            uploadfile = params['uploadfile']
            del params['uploadfile']
        else: uploadfile = None
        #get signed request
        req = self.__get_signed_oauth_request(method, uri, params)
        
        params.clear()
        
        if method != 'POST':
            url = '?'.join([self.get_subdomain_url(uri), req.to_post_data()])
        else:
            url = self.get_subdomain_url(uri)
            if uploadfile:
                req.set_parameter('uploadfile', uploadfile)
                params.update(req.parameters)
        
        self.request_url = url
        self.oauth_request = req
        return url
    
    def get_login_url(self):
        if PbRequest.get_oauth_token_type(self.oauth_token) != 'req':
            raise PbApiError(message='oauth_token is not a request token')
        return '?'.join((self.__web_login_url,
                         'oauth_token=%s' % self.oauth_token.key))
    
    def get(self, uri, params={}):
        return self.__request('GET', uri, params)
    def post(self, uri, params={}):
        return self.__request('POST', uri, params)
    def put(self, uri, params={}):
        return self.__request('PUT', uri, params)
    def delete(self, uri, params={}):
        return self.__request('DELETE', uri, params)
    
    def __request(self, method, uri, params={}):
        '''
        Actual requst function
        @param method: str GET|POST|PUT|DELETE
        @param uri: str uri path
        @param params: dict request params
        @return: string Api response
        '''
        method = method.upper()
        request_params = params
        url = self.__pre_request(method, uri, request_params)
        self.__response_headers, content =\
            self.__raw_request(method, url, request_params)
        return content
    
    def __raw_request(self, method, url, params={}):
        if method == 'POST':
            if self.__detect_file_upload_params(params):
                headers, payload = self.__multipart_encode(params)
            else:
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                payload = self.oauth_request.to_post_data()
        else:
            headers, payload = ({}, None)
        return self.__request_with_redirect(url, method, payload, headers)
    
    def __request_with_redirect(self, url, method, payload, headers):
        '''
        httplib2 chokes on pb api servers redirect header responses
        ( it tries to decompress the content of the response even though
        it's a blank response with rederect in the header)
        This method catches the exception and tries to redirect
        while resetting our api subdomain
        '''
        try:
            self.__logger.debug("request: %s %s" % (method, url))
            results = self.connection.request(url, method=method, body=payload,
                                              headers=headers,
                                              redirections=self.__MAX_REDIRECTS)
            self.__current_redirect = 0
            return results
        except httplib2.FailedToDecompressContent, err:
            if self.__current_redirect < self.__MAX_REDIRECTS:
                self.__current_redirect += 1
                self.set_subdomain(err.response['location'])
                return self.__request_with_redirect(err.response['location'],
                                                    method, payload, headers)
            raise PbApiErrorRequest(\
                    message="Error requesting from server, too many redirects")
    
    def __multipart_encode(self, params={}):
        boundary = mimetools.choose_boundary()
        headers = {'Content-Type': 'multipart/form-data; boundary=%s' % boundary}
        param_str = []
        
        body_string = StringIO()
        
        for key, val in params.iteritems():
            disp = ''
            if isinstance(val, basestring) and val.startswith('@'):
                file_path = val.lstrip('@')
                filename = os.path.basename(file_path)
                mimetype = self.get_filetype(file_path)
                file = open(file_path, 'rb')
                val = file.read()
                file.close()
                body_string.write('--%s\r\n' % boundary)
                body_string.write('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (key, filename))
                body_string.write('Content-Type: %s\r\n' % mimetype)
                body_string.write('\r\n' + val + '\r\n')
            else:
                body_string.write('--%s\r\n' % boundary)
                body_string.write('Content-Disposition: form-data; name="%s"' % key)
                body_string.write('\r\n\r\n' + str(val) + '\r\n')
        body_string.write('--' + boundary + '--\r\n\r\n')
        payload = body_string.getvalue()
        return (headers, payload)
    
    def __detect_file_upload_params(self, params={}):
        for value in params.itervalues():
            try:
                if value.startswith('@'): return True
            except AttributeError: pass # If it's not a string
        return False
        
    def get_filetype(self, filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    
    def __get_connection(self):
        if not self.__http2:
            self.__http2 = httplib2.Http(".cache")
        return self.__http2
    connection = property(__get_connection, None)
    
    def __get_base_string(self):
        if self.oauth_request:
            return self.oauth_request.base_string
        else:
            return ''
    base_string = property(__get_base_string, None)
    
    @staticmethod
    def get_oauth_token_type(token=None):
        if token is None:
            return False
        if token.key.startswith('req_'): return 'req'
        return 'user'