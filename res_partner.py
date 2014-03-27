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

from openerp.osv import fields,osv
from openerp.tools.translate import _

class res_partner(osv.osv):
    _inherit = 'res.partner'
    
    def copy(self, cr, uid, record_id, default=None, context=None):
        if default is None:
            default = {}

        default.update({'address_id': False})

        return super(res_partner, self).copy(cr, uid, record_id, default, context)

    _columns = {
        'from_ebay': fields.boolean('From eBay', help="Check this box if this contact is a ebay customer."),
        'buyer_user_id': fields.char('BuyerUserID'),
        'address_id': fields.char('Address ID', help="""Unique ID for a user's address in the eBay database.
                                  This value can help prevent the need to store an address multiple times across multiple orders.
                                  The ID changes if a user changes their address."""),
        'address_owner': fields.char('AddressOwner'),
    }

