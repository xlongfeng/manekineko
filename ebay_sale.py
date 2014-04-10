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
        'currency': fields.char('Currency', size=3),
        'adjustment_amount': fields.float('AdjustmentAmount'),
        'amount_paid': fields.float('AmountPaid'),
        'amount_saved': fields.float('AmountSaved'),
        'buyer_checkout_message': fields.text('Message'),
        'cancel_reason': fields.selection([
            ('BuyerCancelOrder', 'BuyerCancelOrder'),
            ('BuyerNoShow', 'BuyerNoShow'),
            ('BuyerNotSchedule', 'BuyerNotSchedule'),
            ('BuyerRefused', 'BuyerRefused'),
            ('CustomCode', 'CustomCode'),
            ('OutOfStock', 'OutOfStock'),
            ('ValetDeliveryIssues', 'ValetDeliveryIssues'),
            ('ValetUnavailable', 'ValetUnavailable'),
            ], 'Cancel Reason'),
        # CheckoutStatus
        'cs_last_modified_time': fields.datetime('LastModifiedTime', readonly=True),
        'cs_ebay_payment_status': fields.selection([
            ('BuyerCreditCardFailed', 'BuyerCreditCardFailed'),
            ('BuyerECheckBounced', 'BuyerECheckBounced'),
            ('BuyerFailedPaymentReportedBySeller', 'BuyerFailedPaymentReportedBySeller'),
            ('CustomCode', 'CustomCode'),
            ('NoPaymentFailure', 'NoPaymentFailure'),
            ('PaymentInProcess', 'PaymentInProcess'),
            ('PayPalPaymentInProcess', 'PayPalPaymentInProcess'),
            ], 'eBayPaymentStatus', readonly=True),
        'cs_payment_method': fields.char('PaymentMethod', readonly=True),
        'cs_status': fields.selection([
            ('Complete', 'Complete'),
            ('CustomCode', 'CustomCode'),
            ('Incomplete', 'Incomplete'),
            ('Pending', 'Pending'),
            ], 'CheckoutStatus Status', readonly=True, select=True),
        'created_time': fields.datetime('CreatedTime'),
        'order_id': fields.char('OrderID'),
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
            ], 'OrderStatus', readonly=True, select=True),
        'paid_time': fields.date('PaidTime'),
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
            ], 'PaymentHoldStatus', readonly=True),
        # ShippingDetails
        # SellingManagerSalesRecordNumber
        'sd_record_number': fields.integer('Record Number'),
        'shipped_time': fields.date('ShippedTime'),
        'subtotal': fields.float('Subtotal'),
        'total': fields.float('Total'),
        # TransactionArray
        'transactions': fields.one2many('ebay.sale.order.transaction', 'order_id', 'Order Transactions', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'partner_id': fields.many2one('res.partner', 'Customer', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True, change_default=True, select=True, track_visibility='always'),
        'ebay_user_id': fields.many2one('ebay.user', 'eBay User', states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, select=True, track_visibility='onchange'),
        'state': fields.selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('done', 'Done'),
            ], 'Status', readonly=True, track_visibility='onchange',
            help="Gives the status of the quotation or sales order. \nThe 'Waiting Schedule' status is set when the invoice is confirmed but waiting for the scheduler to run on the order date.", select=True),
    }
    
    _defaults = {
        'name': lambda obj, cr, uid, context: '/',
    }
    
    _order = 'sd_record_number desc'
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'ebay.sale.order') or '/'
        return super(ebay_sale_order, self).create(cr, uid, vals, context=context)
    
ebay_sale_order()

class ebay_sale_order_transaction(osv.osv):
    _name = "ebay.sale.order.transaction"
    _description = "eBay order transaction"
    
    _columns = {
        'name': fields.text('Description', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'actual_handling_cost': fields.float('ActualHandlingCost'),
        'actual_shipping_cost': fields.float('ActualShippingCost'),
        'created_date': fields.datetime('CreatedDate'),
        'final_value_fee': fields.float('FinalValueFee'),
        # Item
        'item_id': fields.char('Item ID', size=38, readonly=True),
        'order_line_item_id': fields.char('OrderLineItemID'),
        'quantity_purchased': fields.integer('Quantity Purchased'),
        'shipped_time': fields.date('ShippedTime'),
        # ShippingDetails
        # selling manager sales record number
        'sd_record_number': fields.integer('Record Number'),
        'transaction_id': fields.char('TransactionID'),
        'transaction_price': fields.float('TransactionPrice'),
        'view_item_url': fields.char('View Item URL', readonly=True),
        
        'order_id': fields.many2one('ebay.sale.order', 'Order Reference', required=True, ondelete='cascade', select=True, readonly=True, states={'draft':[('readonly',False)]}),
        'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)], change_default=True),
        'order_partner_id': fields.related('order_id', 'partner_id', type='many2one', relation='res.partner', store=True, string='Customer'),
        'ebay_user_id':fields.related('order_id', 'ebay_user_id', type='many2one', relation='ebay.user', store=True, string='eBay User'),
        'state': fields.selection([('cancel', 'Cancelled'),('draft', 'Draft'),('confirmed', 'Confirmed'),('exception', 'Exception'),('done', 'Done')], 'Status', required=True, readonly=True,
                help='* The \'Draft\' status is set when the related sales order in draft status. \
                    \n* The \'Confirmed\' status is set when the related sales order is confirmed. \
                    \n* The \'Exception\' status is set when the related sales order is set as exception. \
                    \n* The \'Done\' status is set when the sales order line has been picked. \
                    \n* The \'Cancelled\' status is set when a user cancel the sales order related.'),
    }
    _defaults = {
    }
    
    _order = 'sd_record_number desc'
    
ebay_sale_order_transaction()