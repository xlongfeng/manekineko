'''
Created on Apr 11, 2009

@author: rowhite
'''
import urllib


def normalize_parameters(params, delim='&'):
    '''
    Take a dict of parameters, sorts and encodes them and returns as a str
    @param params: dict or str request parameters
    @param delim: str delimiter between parameters in return string 
                    (headers use ',')
    @rtype: str
    '''
    if isinstance(params, str):
        try:
            from urlparse import parse_qs
        except ImportError:
            from cgi import parse_qs
        params = parse_qs(params, True)
        
    keys_values = params.items()
    keys_values.sort()
    return delim.join([_encode_parameter(key, value) \
                     for key, value in keys_values])


def _encode_parameter(key, value):
    # parameter values may be a list, need to sort and include
    #  each individually
    if isinstance(value, list):
        values = value
        values.sort()
    else:
        values = [value]
    return '&'.join(['%s=%s' % (urlencode_rfc3986(key),
                                urlencode_rfc3986_utf8(val))\
                                for val in values])


def urlencode_rfc3986(string):
    return urllib.quote(string, '~')


def urlencode_rfc3986_utf8(string):
    if isinstance(string, unicode):
        return urlencode_rfc3986(string.encode('utf-8'))
    else:
        return urlencode_rfc3986(str(string))


def urldecode_rfc3986(string):
    return urllib.unquote(string)


def get_filtered_base_string_params(params):
    """
    Filter params that don't belong in base string
    @param params: dict of key value parameters
    """
    try:
        del params['oauth_signature']
    except:
        pass
    return params


if __name__ == '__main__':
    results = normalize_parameters("name")
    print results