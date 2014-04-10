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

class sale_order(osv.osv):
    _inherit = "sale.order"

    _columns = {
        'adjustment_amount': fields.float('AdjustmentAmount'),
        'amount_paid': fields.float('AmountPaid'),
        'amount_saved': fields.float('AmountSaved'),
        'buyer_checkout_message': fields.text('Message'),
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
        # selling manager sales record number
        'sd_record_number': fields.integer('Record Number'),
        'shipped_time': fields.date('ShippedTime'),
        'subtotal': fields.float('Subtotal'),
        'total': fields.float('Total'),
    }
    _defaults = {
    }

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    
    _columns = {
        'actual_handling_cost': fields.float('ActualHandlingCost'),
        'actual_shipping_cost': fields.float('ActualShippingCost'),
        # Item
        'item_id': fields.char('Item ID', size=38, readonly=True),
        'order_line_item_id': fields.char('OrderLineItemID'),
        # ShippingDetails
        # selling manager sales record number
        'sd_record_number': fields.integer('Record Number'),
        'transaction_id': fields.char('TransactionID'),
        'transaction_price': fields.float('TransactionPrice'),
        'view_item_url': fields.char('View Item URL', readonly=True),
    }
    _defaults = {
    }