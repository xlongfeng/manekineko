'''
Created on May 5, 2009

@author: rowhite
'''
try:
    from collections import defaultdict
except:
    # via recipe at http://code.activestate.com/recipes/523034/
    class defaultdict(dict):
        def __init__(self, default_factory=None, *a, **kw):
            if (default_factory is not None and
                not hasattr(default_factory, '__call__')):
                raise TypeError('first argument must be callable')
            dict.__init__(self, *a, **kw)
            self.default_factory = default_factory
        def __getitem__(self, key):
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                return self.__missing__(key)
        def __missing__(self, key):
            if self.default_factory is None:
                raise KeyError(key)
            self[key] = value = self.default_factory()
            return value
        def __reduce__(self):
            if self.default_factory is None:
                args = tuple()
            else:
                args = self.default_factory,
            return type(self), args, None, None, self.items()
        def copy(self):
            return self.__copy__()
        def __copy__(self):
            return type(self)(self.default_factory, self)
        def __deepcopy__(self, memo):
            import copy
            return type(self)(self.default_factory,
                              copy.deepcopy(self.items()))
        def __repr__(self):
            return 'defaultdict(%s, %s)' % (self.default_factory,
                                            dict.__repr__(self))

from error import *

class PbResponse(object):
    '''
    Abstract Response parser object from pb API
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        pass

    def parse(self, string, onlycontent=False):
        raise NotImplementedError
    
    def _detect_exception(self, data={}):
        if 'status' in data and data['status'] != 'OK':
            raise PbApiErrorResponse(data.get('message'), data.get('code'))
    
    def get_format(self):
        raise NotImplementedError

class Json(PbResponse):
    '''
    response json format parser
    Requires python 2.6+ or simplejson package
    '''
    
    def parse(self, string, onlycontent=False):
        try:
            import json
        except ImportError:
            import simplejson as json
        result = json.loads(string)
        self._detect_exception(result)
        if onlycontent:
            return result['content']
        return result
        
    
    def get_format(self):
        return 'json'
    format = property(get_format, None)

class Xmldom(PbResponse):
    '''
    response xml format parser
    uses minidom
    '''
    
    def parse(self, string, onlycontent=False):
        from xml.dom.minidom import parseString
        dom = parseString(string)
        self._detect_exception(dom)
        
        if onlycontent:
            return dom.getElementsByTagName('content')[0]
        return dom.documentElement
    
    def _detect_exception(self, dom):
        try:
            status = dom.getElementsByTagName('status')[0].firstChild.data
        except IndexError:
            raise PbApiErrorResponse("Unable to parse response status")
        if status != u'OK':
            message = dom.getElementsByTagName('message')[0].firstChild.data
            code = dom.getElementsByTagName('code')[0].firstChild.data
            raise PbApiErrorResponse(message, code)
    
    def get_format(self):
        return 'xml'
    format = property(get_format, None)


class Xmldomdict(Xmldom):
    '''
    response xml format parser
    converst dom to a simple dict
    '''
    
    def parse(self, string, onlycontent=False):
        elem = super(Xmldomdict, self).parse(string, onlycontent)
        return self.xmlToDict(elem)
    
    def xmlToDict(self, node):
        results = {}
        attr_map = node.attributes
        node.normalize()
        attribs = {}
        if attr_map:
            for i in range(attr_map.length):
                attribs[attr_map.item(i).name] = attr_map.item(i).value
        if node.hasChildNodes():
            if attribs: results['_attribs'] = attribs
            # prescan children for multiple tags of same name
            childnums = defaultdict(int)
            for child in node.childNodes:
                if child.nodeType == child.TEXT_NODE: continue
                childnums[child.nodeName] += 1
                
            if not childnums:
                # only text children (leaf)
                if attribs:
                    results['content'] = node.firstChild.data
                else:
                    results = node.firstChild.data
                    
            # build dicts for children
            for child in node.childNodes:
                if child.nodeType == child.TEXT_NODE: continue
                if childnums[child.nodeName] > 1:
                    if child.nodeName not in results:
                        results[child.nodeName] = []
                    results[child.nodeName].append(self.xmlToDict(child))
                else:
                    results[child.nodeName] = self.xmlToDict(child)
        else: results = attribs
        return results

class Xmletree(PbResponse):
    '''
    response xml format parser based on ElementTree
    '''
    def parse(self, string, onlycontent=False):
        import xml.etree.ElementTree
        tree = xml.etree.ElementTree.XML(string)
        self._detect_exception(tree)
        if onlycontent:
            return tree.find('content')
        return tree
        
    def _detect_exception(self, tree):
        if tree.findtext('status') != 'OK':
            message = tree.findtext('message')
            code = tree.findtext('code')
            raise PbApiErrorResponse(message, code)
    def get_format(self):
        return 'xml'
    format = property(get_format, None)
