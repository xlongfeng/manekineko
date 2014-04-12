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
    
    def _get_shipping_service_type(self, cr, uid, context=None):
        return self.pool.get('ebay.user').get_shipping_service_type()

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
        'shipping_service': fields.selection(
            _get_shipping_service_type, 'Shipping service', readonly=True, states={'draft': [('readonly', False)], 'progress': [('readonly', False)], 'pending': [('readonly', False)]}
        ),
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
    
    def _prepare_order_picking(self, cr, uid, order, context=None):
        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
        return {
            'name': pick_name,
            'origin': order.name,
            'date': order.created_time,
            'type': 'out',
            'state': 'draft',
            'move_type': 'one',
            'partner_id': order.partner_id.id,
            'note': order.buyer_checkout_message,
            'invoice_state': 'none',
        }
    
    def _prepare_order_line_move(self, cr, uid, order, line, picking_id, ebay_item, context=None):
        warehouse_id = self.pool.get('stock.warehouse').search(cr, uid, [], context=context)[0]
        warehouse = self.pool.get('stock.warehouse').browse(cr, uid, warehouse_id, context=context)
        property_out = order.partner_id.property_stock_customer
        return {
            'name': line.name,
            'picking_id': picking_id,
            'product_id': ebay_item.product_id.id,
            'product_qty': ebay_item.product_uom_qty * line.quantity_purchased,
            'product_uom': ebay_item.product_uom.id,
            'product_uos_qty': ebay_item.product_uom_qty * line.quantity_purchased,
            'product_uos': ebay_item.product_uom.id,
            'location_id': warehouse.lot_stock_id.id,
            'location_dest_id': property_out.id,
            'partner_id': order.partner_id.id,
            'tracking_id': False,
            'state': 'draft',
            #'state': 'waiting',
            'price_unit': line.transaction_price
        }
    
    def _create_pickings(self, cr, uid, order, context=None):
        if (order.state == 'draft' or order.state == 'pending') \
            and order.cs_ebay_payment_status == 'NoPaymentFailure' and order.cs_status == 'Complete':
            move_obj = self.pool.get('stock.move')
            picking_obj = self.pool.get('stock.picking')
            
            # check all line avaiable
            for line in order.transactions:
                if line.ebay_item_variation_id:
                    ebay_item_id = line.ebay_item_variation_id
                    product_id = ebay_item_id.product_id
                elif line.ebay_item_id:
                    ebay_item_id = line.ebay_item_id
                    product_id = ebay_item_id.product_id
                else:
                    return
                
                if not ebay_item_id.exists() or not product_id.exists():
                    return
             
            for line in order.transactions:
                if line.ebay_item_variation_id:
                    ebay_item_id = line.ebay_item_variation_id
                    product_id = ebay_item_id.product_id
                elif line.ebay_item_id:
                    ebay_item_id = line.ebay_item_id
                    product_id = ebay_item_id.product_id
                else:
                    ebay_item_id = False
                    product_id = False
                if ebay_item_id and ebay_item_id.exists() and product_id and product_id.exists():
                    picking_id = picking_obj.create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
                    move_id = move_obj.create(cr, uid, self._prepare_order_line_move(cr, uid, order, line, picking_id, ebay_item_id, context=context))
                    order.write({'state': 'progress'})
    
    def action_confirm(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            self._create_pickings(cr, uid, order, context=context)
        return True
        
    def action_pending(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'pending'}, context)
        
    def action_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'cancel'}, context)
        
    def action_send(self, cr, uid, ids, context=None):
        send_ids = list()
        for order in self.browse(cr, uid, ids, context=context):
            if order.state == 'progress':
                send_ids.append(order.id)
        return self.write(cr, uid, send_ids, {'state': 'sent'}, context)
        
    def action_done(self, cr, uid, ids, context=None):
        done_ids = list()
        for order in self.browse(cr, uid, ids, context=context):
            if order.state == 'sent':
                done_ids.append(order.id)
        return self.write(cr, uid, done_ids, {'state': 'done'}, context)
    
ebay_sale_order()

class ebay_sale_order_transaction(osv.osv):
    _name = "ebay.sale.order.transaction"
    _description = "eBay order transaction"
    
    def _get_variation(self, cr, uid, ids, field_name, arg, context):
        if context is None:
            context = {}
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = record.ebay_item_id.variation
        return res
    
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
        'ebay_item_id': fields.many2one('ebay.item', 'Item', domain=[('state', '=', 'Active')], change_default=True),
        'ebay_item_variation_id': fields.many2one('ebay.item', 'Variation', domain="[('parent_id', '=', ebay_item_id)]", change_default=True),
        'variation': fields.function(_get_variation, type='boolean', method="True", string='Variation'),
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
    
    def on_change_ebay_item_id(self, cr, uid, id, ebay_item_id, context=None):
        value = dict()
        item = self.pool.get('ebay.item').browse(cr, uid, ebay_item_id, context=context)
        value['name'] = item.name
        value['ebay_item_variation_id'] = False
        value['variation'] = item.variation
        value['transaction_price'] = item.start_price
        return {
            'value': value
        }
    
    def on_change_ebay_item_variation_id(self, cr, uid, id, ebay_item_id, ebay_item_variation_id, context=None):
        value = dict()
        item = self.pool.get('ebay.item').browse(cr, uid, [ebay_item_id, ebay_item_variation_id], context=context)
        value['name'] = '%s%s' % (item[0].name, item[1].name)
        value['transaction_price'] = item[1].start_price
        return {
            'value': value
        }

ebay_sale_order_transaction()