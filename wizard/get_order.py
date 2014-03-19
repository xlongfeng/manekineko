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

class get_order(osv.TransientModel):
    _name = 'ebay.getorder'
    _description = 'eBay Get Orders'
    
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
    
    def action_sync(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        print 'b' * 30
        data = self.read(cr, uid, ids)[0]
        print data
        ebay_ebay_obj = self.pool.get('ebay.ebay')
        for user in ebay_ebay_obj.get_auth_user(cr, uid, data['sandbox_user_included'], context=context):
            output_selector = [
                'HasMoreOrders',
                'OrderArray.Order.AdjustmentAmount',
                'OrderArray.Order.AmountPaid',
                'OrderArray.Order.AmountSaved',
                'OrderArray.Order.BuyerCheckoutMessage',
                'OrderArray.Order.BuyerUserID',
                'OrderArray.Order.CancelReason',
                'OrderArray.Order.CheckoutStatus',
                'OrderArray.Order.CreatedTime',
                'OrderArray.Order.CreatingUserRole',
                'OrderArray.Order.OrderID',
                'OrderArray.Order.OrderStatus',
                'OrderArray.Order.PaidTime',
                'OrderArray.Order.PaymentHoldStatus',
                'OrderArray.Order.ShippedTime',
                'OrderArray.Order.ShippingAddress',
                'OrderArray.Order.ShippingDetails.SellingManagerSalesRecordNumber',
                'OrderArray.Order.Subtotal',
                'OrderArray.Order.Total',
                'OrderArray.Order.TransactionArray.Transaction.ActualHandlingCost',
                'OrderArray.Order.TransactionArray.Transaction.ActualShippingCost',
                'OrderArray.Order.TransactionArray.Transaction.Buyer',
                'OrderArray.Order.TransactionArray.Transaction.CreatedDate',
                'OrderArray.Order.TransactionArray.Transaction.FinalValueFee',
                'OrderArray.Order.TransactionArray.Transaction.Item',
                'OrderArray.Order.TransactionArray.Transaction.OrderLineItemID',
                'OrderArray.Order.TransactionArray.Transaction.QuantityPurchased',
                'OrderArray.Order.TransactionArray.Transaction.ShippedTime',
                'OrderArray.Order.TransactionArray.Transaction.ShippingDetails.SellingManagerSalesRecordNumber',
                'OrderArray.Order.TransactionArray.Transaction.Status',
                'OrderArray.Order.TransactionArray.Transaction.TransactionID',
                'OrderArray.Order.TransactionArray.Transaction.TransactionPrice',
                'OrderArray.Order.TransactionArray.Transaction.UnpaidItem',
                'OrderArray.Order.TransactionArray.Transaction.Variation',
                'OrdersPerPage',
                'PageNumber',
                'ReturnedOrderCountActual',
            ]
            entries_per_page = 75
            page_number = 1
            has_more_orders = True
            while has_more_orders:
                call_data=dict()
                call_data['IncludeFinalValueFee'] = True
                call_data['NumberOfDays'] = data['number_of_days']
                order_status = data['order_status']
                if order_status:
                    call_data['OrderStatus'] = order_status
                call_data['Pagination'] = {
                    'EntriesPerPage': entries_per_page,
                    'PageNumber': page_number,
                }
                error_msg = 'Get the orders for the specified user %s' % user.name
                resp = ebay_ebay_obj.call(cr, uid, user, 'GetOrders', call_data, error_msg, context=context)
                has_more_orders = resp.HasMoreOrders == 'true'
                ebay_ebay_obj.dump_resp(cr, uid, resp)
                page_number = page_number + 1

        return {'type': 'ir.actions.act_window_close'}

get_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: