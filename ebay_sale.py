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
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
from openerp import netsvc
from openerp.tools.translate import _
import pytz
from openerp import SUPERUSER_ID

class ebay_sale_order(osv.osv):
    _name = "ebay.sale.order"
    _description = "eBay order"

    _columns = {
        'name': fields.char('Order Reference', size=64, required=True,
            readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, select=True),
        'currency': fields.char('Currency', size=3, readonly=True),
        'adjustment_amount': fields.float('Adjustment Amount', readonly=True),
        'amount_paid': fields.float('Amount Paid', readonly=True),
        'amount_saved': fields.float('Amount Saved', readonly=True),
        'buyer_checkout_message': fields.text('Message', readonly=True),
        'buyer_user_id': fields.char('User ID', readonly=True, states={'draft': [('readonly', False)]}),
        'cancel_reason': fields.selection([
            ('BuyerCancelOrder', 'BuyerCancelOrder'),
            ('BuyerNoShow', 'BuyerNoShow'),
            ('BuyerNotSchedule', 'BuyerNotSchedule'),
            ('BuyerRefused', 'BuyerRefused'),
            ('CustomCode', 'CustomCode'),
            ('OutOfStock', 'OutOfStock'),
            ('ValetDeliveryIssues', 'ValetDeliveryIssues'),
            ('ValetUnavailable', 'ValetUnavailable'),
            ], 'Cancel Reason', readonly=True),
        # CheckoutStatus
        'cs_last_modified_time': fields.datetime('Last Modified Time', readonly=True),
        'cs_ebay_payment_status': fields.selection([
            ('BuyerCreditCardFailed', 'BuyerCreditCardFailed'),
            ('BuyerECheckBounced', 'BuyerECheckBounced'),
            ('BuyerFailedPaymentReportedBySeller', 'BuyerFailedPaymentReportedBySeller'),
            ('CustomCode', 'CustomCode'),
            ('NoPaymentFailure', 'NoPaymentFailure'),
            ('PaymentInProcess', 'PaymentInProcess'),
            ('PayPalPaymentInProcess', 'PayPalPaymentInProcess'),
            ], 'Payment Status', readonly=True),
        'cs_payment_method': fields.char('Payment Method', readonly=True),
        'cs_status': fields.selection([
            ('Complete', 'Complete'),
            ('CustomCode', 'CustomCode'),
            ('Incomplete', 'Incomplete'),
            ('Pending', 'Pending'),
            ], 'Checkout Status', readonly=True, select=True),
        'created_time': fields.datetime('Created Time', readonly=True),
        'order_id': fields.char('Order ID', readonly=True),
        'order_status': fields.selection([
            ('Active', 'Active'),
            ('All', 'All'),
            ('Authenticated', 'Authenticated'),
            ('Cancelled', 'Cancelled'),
            ('Completed', 'Completed'),
            ('CustomCode', 'CustomCode'),
            ('Default', 'Default'),
            ('Inactive', 'Inactive'),
            ('InProcess', 'InProcess'),
            ('Invalid', 'Invalid'),
            ('Shipped', 'Shipped'),
            ], 'Order Status', readonly=True, select=True),
        'paid_time': fields.datetime('Paid Time', readonly=True),
        'payment_hold_status':  fields.selection([
            ('CustomCode', 'CustomCode'),
            ('MerchantHold', 'MerchantHold'),
            ('NewSellerHold', 'NewSellerHold'),
            ('None', 'None'),
            ('PaymentHold', 'PaymentHold'),
            ('PaymentReview', 'PaymentReview'),
            ('ReleaseConfirmed', 'ReleaseConfirmed'),
            ('Released', 'Released'),
            ('ReleasePending', 'ReleasePending'),
            ], 'Payment Hold Status', readonly=True),
        # ShippingDetails
        # SellingManagerSalesRecordNumber
        'sd_record_number': fields.integer('Record Number', readonly=True),
        'shipped_time': fields.datetime('Shipped Time', readonly=True),
        'subtotal': fields.float('Subtotal', readonly=True),
        'total': fields.float('Total', readonly=True),
        # TransactionArray
        'transactions': fields.one2many('ebay.sale.order.transaction', 'order_id', 'Transactions', readonly=True, states={'draft': [('readonly', False)]}),
        'partner_id': fields.many2one('res.partner', 'Customer', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True, change_default=True, select=True, track_visibility='always'),
        'ebay_user_id': fields.many2one('ebay.user', 'eBay User', states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, select=True, track_visibility='onchange'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('progress', 'In Progress'),
            ('sent', 'Sent'),
            ('cancel', 'Cancelled'),
            ('pending', 'Pending'),
            ('done', 'Done'),
            ], 'Status', readonly=True, track_visibility='onchange',
            help="Gives the status of the quotation or sales order. \nThe 'Waiting Schedule' status is set when the invoice is confirmed but waiting for the scheduler to run on the order date.", select=True),
    }
    
    _defaults = {
        'name': lambda obj, cr, uid, context: '/',
        'created_time': fields.datetime.now(),
        'state': 'draft',
    }
    
    _order = 'sd_record_number desc'
    
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        
        default.update({
            'order_id': '',
            'state': 'draft',
        })

        return super(ebay_sale_order, self).copy(cr, uid, id, default, context)
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/')=='/':
            sd_record_number = vals.get('sd_record_number',0) 
            if sd_record_number:
                vals['name'] = 'eso/%s' % sd_record_number
        return super(ebay_sale_order, self).create(cr, uid, vals, context=context)
    
    def action_confirm(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'progress'}, context)
        
    def action_pending(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'pending'}, context)
        
    def action_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'cancel'}, context)
        
    def action_send(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'sent'}, context)
        
    def action_done(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'done'}, context)
    
ebay_sale_order()

class ebay_sale_order_transaction(osv.osv):
    _name = "ebay.sale.order.transaction"
    _description = "eBay order transaction"
    
    _columns = {
        'name': fields.char('Description', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'actual_handling_cost': fields.float('Handling Cost'),
        'actual_shipping_cost': fields.float('Shipping Cost'),
        'created_date': fields.datetime('Created Date'),
        'final_value_fee': fields.float('Final Value Fee'),
        # Item
        'item_id': fields.char('Item ID', size=38, readonly=True),
        'order_line_item_id': fields.char('OrderLineItemID'),
        'quantity_purchased': fields.integer('Quantity'),
        'shipped_time': fields.datetime('Shipped Time'),
        # ShippingDetails
        # selling manager sales record number
        'sd_record_number': fields.integer('Record Number'),
        'transaction_id': fields.char('TransactionID'),
        'transaction_price': fields.float('Price'),
        'view_item_url': fields.char('View Item URL', readonly=True),
        
        'order_id': fields.many2one('ebay.sale.order', 'Order Reference', required=True, ondelete='cascade', select=True, readonly=True, states={'draft':[('readonly',False)]}),
        'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)], change_default=True),
        'ebay_item_id': fields.many2one('ebay.item', 'Item', change_default=True),
        'order_partner_id': fields.related('order_id', 'partner_id', type='many2one', relation='res.partner', store=True, string='Customer'),
        'ebay_user_id':fields.related('order_id', 'ebay_user_id', type='many2one', relation='ebay.user', store=True, string='eBay User'),
        'state': fields.selection([('draft', 'Draft'),('confirmed', 'Confirmed'),('cancel', 'Cancelled'),('exception', 'Exception'),('done', 'Done')], 'Status', required=True, readonly=True,
                help='* The \'Draft\' status is set when the related sales order in draft status. \
                    \n* The \'Confirmed\' status is set when the related sales order is confirmed. \
                    \n* The \'Exception\' status is set when the related sales order is set as exception. \
                    \n* The \'Done\' status is set when the sales order line has been picked. \
                    \n* The \'Cancelled\' status is set when a user cancel the sales order related.'),
    }
    
    _defaults = {
        'created_date': fields.datetime.now(),
        'quantity_purchased': 1,
        'state': 'draft'
    }
    
    _order = 'sd_record_number desc'
    
ebay_sale_order_transaction()