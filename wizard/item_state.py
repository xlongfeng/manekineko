# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from openerp import tools
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

class ebay_item_sync(osv.TransientModel):
    _name = 'ebay.item.sync'
    _description = 'eBay item sync'
    
    _columns = {
        'count': fields.integer('Item record count', readonly=True),
    }
    
    def _get_count(self, cr, uid, context=None):
        if context is None:
            context = {}
        record_ids = context and context.get('active_ids', False)
        return len(record_ids)
    
    _defaults = {
        'count': _get_count,
    }
    
    def action_sync(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        record_ids = context and context.get('active_ids', False)
        self.pool.get('ebay.item').action_synchronize(cr, uid, record_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}

ebay_item_sync()

class ebay_item_revise(osv.TransientModel):
    _name = 'ebay.item.revise'
    _description = 'eBay item revise'
    
    _columns = {
        'count': fields.integer('Item record count', readonly=True),
    }
    
    def _get_count(self, cr, uid, context=None):
        if context is None:
            context = {}
        record_ids = context and context.get('active_ids', False)
        return len(record_ids)
    
    _defaults = {
        'count': _get_count,
    }
    
    def action_revise(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        record_ids = context and context.get('active_ids', False)
        self.pool.get('ebay.item').action_revise(cr, uid, record_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}

ebay_item_revise()

class ebay_item_end(osv.TransientModel):
    _name = 'ebay.item.end'
    _description = 'eBay item end'
    
    _columns = {
        'count': fields.integer('Item record count', readonly=True),
    }
    
    def _get_count(self, cr, uid, context=None):
        if context is None:
            context = {}
        record_ids = context and context.get('active_ids', False)
        return len(record_ids)
    
    _defaults = {
        'count': _get_count,
    }
    
    def action_end(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        record_ids = context and context.get('active_ids', False)
        self.pool.get('ebay.item').action_end_listing(cr, uid, record_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}

ebay_item_end()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: