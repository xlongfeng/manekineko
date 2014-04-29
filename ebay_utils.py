# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import os
import sys
from datetime import datetime, timedelta

from jinja2 import Template

from openerp import tools
from openerp.osv import fields, orm

def ebay_str_split(s, sep):
    if not s:
        return list()
    if sep == '\n':
        s_list = s.splitlines()
    else:
        s_list = s.split(sep)
    d = list()
    for l in s_list:
        d.append(l.strip())
    return d

def ebay_repeatable_list(repeatable):
    if type(repeatable) != list:
        repeatable = [repeatable]
    return repeatable

def ebay_repeatable(repeatable):
    if type(repeatable) != list:
        raise orm.except_orm(_('Warning!'), _('type %s is not list') % type(repeatable))
    count = len(repeatable)
    if count == 0:
        return False
    elif count == 1:
        return repeatable[0]
    else:
        return repeatable

def ebay_strftime(timestamp):
    if type(timestamp) == datetime:
        return timestamp.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
    else:
        return timestamp
    
def ebay_strptime(timestamp):
    if type(timestamp) == datetime:
        return timestamp
    else:
        return datetime.strptime(timestamp.partition('.')[0], tools.DEFAULT_SERVER_DATETIME_FORMAT)
    
def ebay_dump(api):
    if api.warnings():
        print("Warnings" + api.warnings())
    
    print("Response code: %s" % api.response_code())
    print("Response ETREE: %s" % api.response.dom())
    
    print(api.response.content)
    print(api.response.json())
    
def ebay_errors(errors):
    errors = ebay_repeatable_list(errors)
        
    template = '''
<h2>{{ error.ShortMessage }}</h2>
<ul>
  <li><b>{{ error.LongMessage }}</b></li>
  <li>Error Classification: {{ error.ErrorClassification }}</li>
  <li>Severity Code: {{ error.SeverityCode }}</li>
  <li>Error Code: {{ error.ErrorCode }}</li>
{% if error_parameters %}
  <li>
    <ul>
    {% for error_parameter in error_parameters %}
      <li>{{ error_parameter._ParamID }}: {{ error_parameter.Value }}</li>
    {% endfor %}
    </ul>
  </li>
{% endif %}
</ul>
    '''
    e = ''
    t = Template(template)
    for error in errors:
        if error.has_key('ErrorParameters'):
            error_parameters = error.ErrorParameters
            if type(error_parameters) != list:
                error_parameters = [error_parameters]
        else:
            error_parameters = []
        e += t.render(
        error=error,
        error_parameters=error_parameters,
    )
    return e

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
