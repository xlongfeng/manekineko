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

from openerp import tools
from openerp.osv import fields, orm

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

def ebay_strftime():
    if type(timestamp) == datetime:
        return timestamp.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
    else:
        return timestamp
    
def ebay_strptime(timestamp):
    if type(timestamp) == datetime:
        return timestamp
    else:
        return datetime.strptime(timestamp, tools.DEFAULT_SERVER_DATETIME_FORMAT)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
