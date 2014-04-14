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

class ebay_sale_order_list_print(osv.TransientModel):
    _name = 'ebay.sale.order.list.print'
    _description = 'ebay sale order list print'
    
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
        return {'type': 'ir.actions.act_window_close'}

ebay_sale_order_list_print()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: