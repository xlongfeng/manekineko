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

from datetime import datetime
import base64
import cStringIO

import xlwt

from openerp import tools
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

from openerp.addons.ebay.ebay_utils import *

class export_order(osv.TransientModel):
    _name = 'ebay.exportorder'
    _description = 'eBay Export Orders'
    
    _columns = {
        'start_date': fields.date('Start Date', required=True),
        'end_date': fields.datetime('End Date', required=True),
        'sandbox_user_included': fields.boolean ('Sandbox User Included'),
        'name': fields.char('Filename', readonly=True),
        'data': fields.binary('File', readonly=True),
        'state': fields.selection([
            ('option', 'option'),
            ('download', 'download'),
        ], 'State'),
    }
    
    _defaults = {
        'sandbox_user_included': False,
        'state': 'option'
    }
    
    def action_export(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        this = self.browse(cr, uid, ids)[0]
        ebay_sale_order_obj = self.pool.get('ebay.sale.order')
        
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Order Products')
        
        headers = [
            'Reference',
            'Transaction',
            'SaleDate',
            'Product',
            'Price',
            'Quantity',
            'TotalPrice',
        ]
        
        header_width = {
            'Transaction': (1 + 80) * 256,
            'Product': (1 + 64) * 256,
        }
        
        for i, name in enumerate(headers):
            worksheet.write(0, i, name)
            width = header_width.get(name, 0)
            width = width if width else (1 + 16) * 256
            worksheet.col(i).width = width
            
            
        domain = [('shipped_time', '>', this.start_date), ('shipped_time', '<', this.end_date)]
        order_ids = ebay_sale_order_obj.search(cr, uid, domain, context=context)
        total_price = 0.0
        total_orders = 0
        if order_ids:
            row = 1
            for ebay_sale_order in ebay_sale_order_obj.browse(cr, uid, order_ids, context=context):
                reference = ebay_sale_order.name
                total_orders += 1
                for transaction in ebay_sale_order.transactions:
                    details = transaction.name
                    if transaction.ebay_item_variation_id:
                        ebay_products = transaction.ebay_item_variation_id.product_ids
                    else:
                        ebay_products = transaction.ebay_item_id.product_ids
                    quantity_purchased = transaction.quantity_purchased
                    for ebay_product in ebay_products:
                        product = ebay_product.product_id.name
                        price = ebay_product.product_id.lst_price
                        uos_coeff = ebay_product.uos_coeff
                        worksheet.write(row, 0, reference)
                        worksheet.write(row, 1, details)
                        worksheet.write(row, 2, ebay_sale_order.paid_time)
                        worksheet.write(row, 3, product)
                        worksheet.write(row, 4, price)
                        worksheet.write(row, 5, uos_coeff * quantity_purchased)
                        worksheet.write(row, 6, price * uos_coeff * quantity_purchased)
                        total_price += (price * uos_coeff * quantity_purchased)
                        row += 1
        row += 1
        worksheet.write(row, 5, 'Total Price')
        worksheet.write(row, 6, total_price)
        row += 1
        worksheet.write(row, 5, 'Total Orders')
        worksheet.write(row, 6, total_orders)
        
        fp = cStringIO.StringIO()
        workbook.save(fp)
        out = base64.encodestring(fp.getvalue())
        fp.close()
        
        this.name = "%s-%s.xls" % ('sale_details', datetime.now().strftime('%Y%m%d-%H%M%S'))
        
        self.write(cr, uid, ids, {'state': 'download',
                                  'data': out,
                                  'name': this.name}, context=context)

        return {
            'name': "Export Orders",
            'type': 'ir.actions.act_window',
            'res_model': 'ebay.exportorder',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

export_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: