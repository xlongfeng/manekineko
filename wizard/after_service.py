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

class after_service(osv.TransientModel):
    _name = 'ebay.after.service'
    _description = 'eBay After Service'
    
    _columns = {
        'number_of_days': fields.selection([
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('5', '5'),
            ('7', '7'),
            ('15', '15'),
            ('30', '30'),
            ], 'Number Of Days'),
        'order_status': fields.selection([
            ('Active', 'Active'),
            ('Cancelled', 'Cancelled'),
            ('Completed', 'Completed'),
            ('Inactive', 'Inactive'),
            ('Shipped', 'Shipped'),
            ], 'Order Status'),
        'sandbox_user_included': fields.boolean ('Sandbox User Included'),
    }
    
    _defaults = {
        'number_of_days': '2',
        'order_status': 'Completed',
        'sandbox_user_included': False,
    }
    
    def view_init(self, cr, uid, fields_list, context=None):
        return False
    
    def action_sync(self, cr, uid, ids, context=None):
        
        return {'type': 'ir.actions.act_window_close'}

get_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: