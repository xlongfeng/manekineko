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

import os
import sys
import logging
from datetime import datetime, timedelta, tzinfo
import dateutil.parser as parser
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time
import pytz

from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round

import openerp.addons.decimal_precision as dp

import base64
import urllib2

import json

sys.path.insert(0, '%s/ebaysdk-python/' % os.path.dirname(__file__))

import ebaysdk
from ebaysdk.utils import getNodeText
from ebaysdk.exception import ConnectionError
from ebaysdk.trading import Connection as Trading

_logger = logging.getLogger(__name__)

class ebay_ebay(osv.osv):
    _name = "ebay.ebay"
    _description = "eBay"
    _site_id_domainname_dict = {
        '0': 'ebay.com',
        '2': 'ebay.ca',
        '3': 'ebay.co.uk',
        '15': 'ebay.au',
        '201': 'ebay.hk',
    }
    
    def to_default_format(self, cr, uid, timestamp, context=None):
        date = (parser.parse(timestamp))
        return date.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
    
    def to_iso8601_format(self, cr, uid, timestamp, context=None):
        date = (parser.parse(timestamp))
        return date.isoformat()
        
    def dump_resp(self, cr, uid, api, context=None):
        print("ebay api dump")

        if api.warnings():
            print("Warnings" + api.warnings())
    
        if api.response.content:
            print("Call Success: %s in length" % len(api.response.content))
    
        print("Response code: %s" % api.response_code())
        print("Response DOM1: %s" % api.response_dom())
        print("Response ETREE: %s" % api.response.dom())
    
        print(api.response.content)
        print(api.response.json())
    
    def _get_domainname_by_site_id(self, cr, uid, site_id, context=None):
        return self._site_id_domainname_dict.get(site_id, self._site_id_domainname_dict['0'])
    
    def get_ebay_sign_in_url(self, cr, uid, site_id, sandbox, ru_name, session_id, context=None):
        url = ''
        domainname = self._get_domainname_by_site_id(self, cr, uid, site_id)
        if sandbox:
            url = 'https://signin.sandbox.%s/ws/eBayISAPI.dll?SignIn&runame=%s&SessID=%s' % (domainname, ru_name, session_id)
        else:
            url = 'https://signin.%s/ws/eBayISAPI.dll?SignIn&runame=%s&SessID=%s' % (domainname, ru_name, session_id)
            
        return url
    
    def get_ebay_api_domain(self, cr, uid, site_id, sandbox, context=None):
        url = ''
        domainname = self._get_domainname_by_site_id(self, cr, uid, site_id)
        if sandbox:
            url = 'api.sandbox.%s' % domainname
        else:
            url = 'api.%s' % domainname
            
        return url
    
    def get_auth_user(self, cr, uid, sandbox_user_included, context=None):
        ebay_user_obj = self.pool.get('ebay.user')
        domain = [('ownership', '=', True), ('ebay_auth_token', '!=', False)]
        if not sandbox_user_included:
            domain.append(('sandbox', '=', False))
        ids = ebay_user_obj.search(cr, uid, domain, context=context)
        if not ids:
            raise osv.except_osv(_('Warning!'), _('Can not find an authorized user'))
            
        return ebay_user_obj.browse(cr, uid, ids, context=context)
    
    def get_arbitrary_auth_user(self, cr, uid, sandbox, context=None):
        ebay_user_obj = self.pool.get('ebay.user')
        ids = ebay_user_obj.search(cr, uid,
                [('sandbox', '=', sandbox), ('ownership', '=', True), ('ebay_auth_token', '!=', False)], context=context)
        if not ids:
            raise osv.except_osv(_('Warning!'), _('Can not find an authorized user'))
            
        return ebay_user_obj.browse(cr, uid, ids[0], context=context)
    
    def call(self, cr, uid, user, call_name, call_data=dict(), error_msg='', files=None, context=None):
        try:
            api = Trading(domain=self.pool.get('ebay.ebay').get_ebay_api_domain(cr, uid, user.sale_site, user.sandbox))
            
            if user.ownership:
                api.config.set('appid', user.app_id, force=True)
                api.config.set('devid', user.dev_id, force=True)
                api.config.set('certid', user.cert, force=True)
            
            if call_name not in ('GetSessionID', 'FetchToken'):
                token = ''
                if user.ownership and user.ebay_auth_token:
                    api.config.set('token', user.ebay_auth_token, force=True)
                else:
                    auth_user = self.get_arbitrary_auth_user(cr, uid, user.sandbox, context)
                    api.config.set('appid', auth_user.app_id, force=True)
                    api.config.set('devid', auth_user.dev_id, force=True)
                    api.config.set('certid', auth_user.cert, force=True)
                    api.config.set('token', auth_user.ebay_auth_token, force=True)
                
            api.execute(call_name, call_data, files=files)
            return api
    
        except ConnectionError as e:
            raise osv.except_osv(_('Warning!'), _('%s: %s' % (error_msg, e)))

ebay_ebay()

class ebay_seller_list(osv.osv):
    _name = "ebay.seller.list"
    _description = "ebay sell"
    
    def _get_thumbnail(self, cr, uid, ids, field_name, arg, context):
        if context is None:
            context = {}
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            link = "http://thumbs3.ebaystatic.com/pict/%s8080.jpg" % record.item_id
            res[record.id] = base64.encodestring(urllib2.urlopen(link).read())
        return res
    
    _columns = {
        'buy_it_now_price': fields.float('Buy It Now Price'),
        'currency': fields.char('Currency ID', size=3),
        'hit_count': fields.integer('Hit Count', readonly=True),
        'item_id': fields.char('Item ID', size=38, readonly=True),
        
        # ListingDetails
        'end_time': fields.datetime('End Time', readonly=True),
        'start_time': fields.datetime('Start Time', readonly=True),
        'view_item_url': fields.char('View Item URL', readonly=True),
        
        'quantity': fields.char('Quantity'),
        
        # SellingStatus
        'quantity_sold': fields.integer('Quantity Sold', readonly=True),
        
        'start_price': fields.float('StartPrice'),
        'name': fields.char('Title', size=80),
        'watch_count': fields.integer('Watch Count', readonly=True),
        
        'user_id': fields.many2one('ebay.user', 'Seller', ondelete='cascade'),
        
        # Additional Info
        'thumbnail': fields.function(_get_thumbnail, type='binary', method="True", string="Thumbnail"),
        'picture': fields.html('Picture', readonly=True),
        'average_monthly_sales': fields.integer('Average Monthly Sales', readonly=True),
    }
    
    _order = 'average_monthly_sales desc'
    
ebay_seller_list()

class ebay_user(osv.osv):
    _name = "ebay.user"
    _description = "a registered eBay user"
    
    _columns = {
        'email': fields.char('Email', size=128, readonly=True),
        'feedback_rating_star': fields.selection([
            ('Blue', 'Blue Star'),
            ('CustomCode', 'Reserved for internal or future use.'),
            ('Green', 'Green Star'),
            ('GreenShooting','Green Shooting Star'),
            ('None', 'No graphic displayed'),
            ('Purple', 'Purple Star'),
            ('PurpleShooting', 'Purple Shooting Star'),
            ('Red', 'Red Star'),
            ('RedShooting', 'Red Shooting Star'),
            ('SilverShooting', 'Silver Shooting Star'),
            ('Turquoise', 'Turquoise Star'),
            ('TurquoiseShooting', 'Turquoise Shooting Star'),
            ('Yellow', 'Yellow Star'),
            ('YellowShooting', 'Yellow Shooting Star')
            ], 'Feedback Rating Star', readonly=True),
        'feedback_score': fields.integer('Feedback Score', readonly=True),
        'positive_feedback_percent': fields.float('Feedback Percent', readonly=True),
        'registration_date': fields.datetime('Registration Date', readonly=True),
        'store_owner': fields.boolean('Store Owner', readonly=True),
        'store_site': fields.char('Store Site', readonly=True),
        'store_url': fields.char('Store URL', readonly=True),
        'top_rated_seller': fields.boolean('Top-rated Seller', readonly=True),
        'site': fields.char('Site', readonly=True),
        'unique_negative_feedback_count': fields.integer('Negative', readonly=True),
        'unique_neutral_feedback_count': fields.integer('Neutral', readonly=True),
        'unique_positive_feedback_count': fields.integer('Positive', readonly=True),
        'name': fields.char('User ID', required=True, select=True),
        # Selleris
        'seller_list_ids': fields.one2many('ebay.seller.list', 'user_id', 'Seller Lists', readonly=True),
        # Application keys for authorization
        'ownership': fields.boolean('Ownership', readonly=True),
        'sandbox': fields.boolean('Sandbox'),
        'sale_site': fields.selection([
            ('0', 'US'),
            ('2', 'Canada'),
            ('3', 'UK'),
            ('15', 'Australia'),
            ('201', 'HongKong'),
            ], 'Sale Site'),
        'app_id': fields.char('AppID', size=64),
        'dev_id': fields.char('DevID', size=64),
        'cert': fields.char('CERT', size=64),
        'ru_name': fields.char('RuName', size=64),
        # Auth info, get from FetchToken
        'session_id': fields.char('SessionID', size=40, readonly=True),
        'ebay_auth_token': fields.char('eBayAuthToken', readonly=True),
        'hard_expiration_time': fields.datetime('HardExpirationTime', readonly=True),
        'rest_token': fields.char('RESTToken', readonly=True),
        # Sale status
        'monthly_sales': fields.float('Monthly Sales', readonly=True),
        'monthly_sales_volume': fields.integer('Monthly Sales Volume', readonly=True),
        # Additional Info
        'ebay_item_ids': fields.one2many('ebay.item', 'ebay_user_id', 'Items'),
        'paypal_email_address': fields.char('Paypal Email Address'),
        'country': fields.char('Country', size=2),
        'location': fields.char('Location'),
        # User Preferences
        'exclude_ship_to_location': fields.text('Exclude Ship To Location', readonly=True),
    }
    
    _defaults = {
        'feedback_score': 0,
        'store_owner': 0,
        'ownership': 0,
        'sandbox': 0,
        'sale_site': '0',
        'country': 'CN',
        'location': 'ShenZhen',
    }
    
    _order = 'monthly_sales desc'
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'User ID must be unique!'),
    ]
    
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        
        name = self.read(cr, uid, id, ['name'], context=context)['name']
        default = default.copy()
        default.update({
            'name': name + _(' (Copy)'),
            'session_id': '',
            'ebay_auth_token': '',
        })

        return super(ebay_user, self).copy(cr, uid, id, default, context)
    
    def action_get_user(self, cr, uid, ids, context=None):
        for user in self.browse(cr, uid, ids, context=context):
            call_data=dict()
            call_data['UserID'] = user.name
            error_msg = 'Get the data for the specified user %s' % user.name
            reply = self.pool.get('ebay.ebay').call(cr, uid, user, 'GetUser', call_data, error_msg, context=context).response.reply
            vals = dict()
            user_dict = reply.User
            vals['email'] = user_dict.Email
            vals['feedback_rating_star'] = user_dict.FeedbackRatingStar
            vals['feedback_score'] = user_dict.FeedbackScore
            vals['positive_feedback_percent'] = user_dict.PositiveFeedbackPercent
            vals['registration_date'] = user_dict.RegistrationDate
            seller_info = user_dict.SellerInfo
            vals['store_owner'] = seller_info.StoreOwner == "true"
            if vals['store_owner']:
                vals['store_site'] = seller_info.StoreSite
                vals['store_url'] = seller_info.StoreURL
            vals['top_rated_seller'] = seller_info.get('TopRatedSeller', False)
            vals['site'] = user_dict.Site
            vals['unique_negative_feedback_count'] = user_dict.UniqueNegativeFeedbackCount
            vals['unique_neutral_feedback_count'] = user_dict.UniqueNeutralFeedbackCount
            vals['unique_positive_feedback_count'] = user_dict.UniquePositiveFeedbackCount
            
            call_data=dict()
            call_data['ShowSellerExcludeShipToLocationPreference'] = 'true'
            error_msg = 'Get the user perferences for the user %s' % user.name
            reply = self.pool.get('ebay.ebay').call(cr, uid, user, 'GetUserPreferences', call_data, error_msg, context=context).response.reply
            exclude_ship_to_location = reply.SellerExcludeShipToLocationPreferences.ExcludeShipToLocation
            if type(exclude_ship_to_location) != list:
                vals['exclude_ship_to_location'] = exclude_ship_to_location
            else:
                vals['exclude_ship_to_location'] = '|'.join(exclude_ship_to_location)
                
            user.write(vals)
    
    def action_get_seller_list(self, cr, uid, ids, context=None):
        for user in self.browse(cr, uid, ids, context=context):
            cr.execute('delete from ebay_seller_list \
                            where user_id=%s', (user.id,))
            monthly_sales = 0.0
            monthly_sales_volume = 0
            output_selector = [
                'HasMoreItems',
                'ItemArray.Item.BuyItNowPrice',
                'ItemArray.Item.Currency',
                'ItemArray.Item.ItemID',
                'ItemArray.Item.ListingDetails.ConvertedStartPrice',
                'ItemArray.Item.ListingDetails.StartTime',
                'ItemArray.Item.ListingDetails.EndTime',
                'ItemArray.Item.ListingDetails.ViewItemURL',
                'ItemArray.Item.ListingType',
                'ItemArray.Item.PictureDetails.PictureURL',
                'ItemArray.Item.PrimaryCategory',
                'ItemArray.Item.Quantity',
                'ItemArray.Item.SellingStatus.QuantitySold',
                'ItemArray.Item.StartPrice',
                'ItemArray.Item.Title',
                'ItemsPerPage',
                'PageNumber',
                'ReturnedItemCountActual',
            ]
            # TODO
            time_now = datetime.now()
            time_now_pdt = datetime.now(pytz.timezone('US/Pacific'))
            end_time_from = time_now_pdt.isoformat()
            end_time_to = (time_now_pdt + timedelta(30)).isoformat()
            entries_per_page = 100
            page_number = 1
            has_more_items = True
            while has_more_items:
                call_data=dict()
                call_data['EndTimeFrom'] = end_time_from
                call_data['EndTimeTo'] = end_time_to
                call_data['IncludeWatchCount'] = True
                call_data['Pagination'] = {
                    'EntriesPerPage': entries_per_page,
                    'PageNumber': page_number,
                }
                call_data['UserID'] = user.name
                call_data['DetailLevel'] = 'ReturnAll'
                call_data['OutputSelector'] = output_selector
                error_msg = 'Get the seller list for the specified user %s' % user.name
                reply = self.pool.get('ebay.ebay').call(cr, uid, user, 'GetSellerList', call_data, error_msg, context=context).response.reply
                ebay_seller_list_obj = self.pool.get('ebay.seller.list')
                has_more_items = reply.HasMoreItems == 'true'
                items = reply.ItemArray.Item
                if type(items) != list:
                    items = [items]
                for item in items:
                    if item.ListingType not in ('FixedPriceItem', 'StoresFixedPrice'):
                        continue
                    vals = dict()
                    vals['buy_it_now_price'] = float(item.BuyItNowPrice.value)
                    vals['currency'] = item.Currency
                    vals['hit_count'] = item.get('HitCount')
                    vals['item_id'] = item.ItemID
                    
                    listing_details = item.ListingDetails
                    vals['end_time'] = listing_details.EndTime
                    start_time = listing_details.StartTime
                    vals['start_time'] = start_time
                    vals['view_item_url'] = listing_details.ViewItemURL
                    
                    vals['quantity'] = int(item.Quantity)
                    
                    selling_status = item.SellingStatus
                    start_price = float(item.StartPrice.value)
                    quantity_sold = int(selling_status.QuantitySold)
                    vals['quantity_sold'] = quantity_sold
                    vals['start_price'] = start_price
                    
                    vals['name'] = item.Title
                    vals['watch_count'] = item.get('WatchCount')
                    vals['user_id'] = user.id
                    
                    delta_days = (time_now - start_time).days
                    if delta_days <= 0:
                        delta_days = 1
                    average_monthly_sales = quantity_sold * 30 / delta_days
                    monthly_sales = monthly_sales + start_price * average_monthly_sales
                    monthly_sales_volume = monthly_sales_volume + average_monthly_sales
                    
                    vals['average_monthly_sales'] = average_monthly_sales
                    
                    picture_details = item.get('PictureDetails')
                    if picture_details:
                        picture_url = picture_details.get('PictureURL', None)
                        if type(picture_url) != list:
                            vals['picture'] = '<img src="%s" width="500"/>' % picture_url
                        else:
                            vals['picture'] = '<img src="%s" width="500"/>' % picture_url[0]
                    
                    ebay_seller_list_obj.create(cr, uid, vals, context=context)
                page_number = page_number + 1
                
            user.write(dict(monthly_sales=monthly_sales, monthly_sales_volume=monthly_sales_volume))
            
ebay_user()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
