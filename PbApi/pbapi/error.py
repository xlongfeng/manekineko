'''
Created on May 6, 2009

@author: rowhite
'''
class PbApiError(RuntimeError):
    '''
    Pb Api related error parent class
    '''
    core = None
    message = None
    code = None
    
    def __init__(self, message='', code='', core=None):
        self.core = core
        self.message = message
        self.code = code
    
    def __str__(self):
        string = ["(%s): %s\n" % \
                  (self.code, self.message)]
        if self.method_stack:
            string.append("Method: %s\n" % ':'.join(self.method_stack))
        if self.params:
            string.append("Params: %s\n" % \
                          ', '.join(['%s => %s' % (key, value) for \
                          key, value in self.params]))
        return ''.join(string)
    
    def get_method_stack(self):
        if self.core:
            return self.core.method_stack
        return None
    method_stack = property(get_method_stack, None)
    
    def get_params(self):
        if self.core:
            return self.core.params
        return None
    params = property(get_params, None)
    

class PbApiErrorResponse(PbApiError):
    '''
    Pb Api error from the response
    '''
    pass

class PbApiErrorRequest(PbApiError):
    '''
    Pb Api error during request
    
    '''
    pass

