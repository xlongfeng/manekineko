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

from requests import exceptions

from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round

import openerp.addons.decimal_precision as dp

import base64
import urllib2

import json

from ebay_utils import *
import ebaysdk
from ebaysdk.parallel import Parallel
from ebaysdk.exception import ConnectionError, ConnectionResponseError
from requests.exceptions import RequestException

_logger = logging.getLogger(__name__)

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
    
    def create_items(self, cr, uid, user, items, context=None):
        monthly_sales = 0
        monthly_sales_volume = 0
        now = datetime.now()
        for item in ebay_repeatable_list(items):
            if item.ListingType not in ('FixedPriceItem', 'StoresFixedPrice'):
                continue
            vals = dict()
            vals['buy_it_now_price'] = float(item.BuyItNowPrice.value)
            vals['currency'] = item.Currency
            vals['hit_count'] = item.HitCount if item.has_key('HitCount') else 0
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
            vals['watch_count'] = item.WatchCount if item.has_key('WatchCount') else 0
            vals['user_id'] = user.id
            
            delta_days = (now - start_time).days
            if delta_days <= 0:
                delta_days = 1
            average_monthly_sales = quantity_sold * 30 / delta_days
            monthly_sales += start_price * average_monthly_sales
            monthly_sales_volume += average_monthly_sales
            
            vals['average_monthly_sales'] = average_monthly_sales
            
            if item.has_key('PictureDetails') and  item.PictureDetails.has_key('PictureURL'):
                picture_url = item.PictureDetails.PictureURL
                vals['picture'] = '<img src="%s" width="500"/>' % ebay_repeatable_list(picture_url)[0]
            
            self.create(cr, uid, vals, context=context)
        return monthly_sales, monthly_sales_volume
    
    def get_seller_list_call(self, cr, uid, user, call_param, parallel=None, context=None):
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
            'PaginationResult',
            'ReturnedItemCountActual',
        ]
        call_name = 'GetSellerList'
        call_data=dict()
        call_data['EndTimeFrom'] = call_param['end_time_from']
        call_data['EndTimeTo'] = call_param['end_time_to']
        call_data['IncludeWatchCount'] = True
        call_data['Pagination'] = {
            'EntriesPerPage': call_param['entries_per_page'],
            'PageNumber': call_param['page_number'],
        }
        call_data['UserID'] = user.name
        call_data['DetailLevel'] = 'ReturnAll'
        call_data['OutputSelector'] = output_selector
        
        api = self.pool.get('ebay.ebay').trading(cr, uid, user, call_name, parallel=parallel, context=context)
        api.execute(call_name, call_data)
        return api
    
    def get_seller_list(self, cr, uid, user, context=None):
        last_updated = user.last_updated
        if last_updated:
            now_time = datetime.now()
            last_updated = datetime.strptime(last_updated, tools.DEFAULT_SERVER_DATETIME_FORMAT)
            delta = (now_time - last_updated).days
            if delta < 7:
                return True
    
        cr.execute('delete from ebay_seller_list \
                        where user_id=%s', (user.id,))
        
        now = datetime.now()
        end_time_from = now.isoformat()
        end_time_to = (now + timedelta(30)).isoformat()
        entries_per_page = 160
        page_number = 1
        
        call_param = dict(
            end_time_from=end_time_from,
            end_time_to=end_time_to,
            entries_per_page=entries_per_page,
            page_number=page_number
        )
        
        reply = self.get_seller_list_call(cr, uid, user, call_param, context=context).response.reply
        total_number_of_pages = int(reply.PaginationResult.TotalNumberOfPages)
        
        if total_number_of_pages == 0:
            return True
        
        monthly_sales, monthly_sales_volume = self.create_items(cr, uid, user, reply.ItemArray.Item, context=context)
        
        page_number = 2
        total_number_of_pages += 1
        while page_number < total_number_of_pages:
            parallel = Parallel()
            multiple_threads = 0
            apis = list()
            while page_number < total_number_of_pages and multiple_threads < 5:
                call_param = dict(
                    end_time_from=end_time_from,
                    end_time_to=end_time_to,
                    entries_per_page=entries_per_page,
                    page_number=page_number
                )
                apis.append(self.get_seller_list_call(cr, uid, user, call_param, parallel=parallel, context=context))
                page_number += 1
                multiple_threads += 1
                
            parallel.wait(60)
                
            for api in apis:
                reply = api.response.reply
                if reply.Ack in ('Success', 'Warning'):
                    _monthly_sales, _monthly_sales_volume = self.create_items(cr, uid, user, reply.ItemArray.Item, context=context)
                    monthly_sales += _monthly_sales
                    monthly_sales_volume += _monthly_sales_volume
                else:
                    raise ConnectionError(api.error())
            
        return user.write(dict(
            last_updated=fields.datetime.now(),
            monthly_sales=monthly_sales,
            monthly_sales_volume=monthly_sales_volume
        ))
    
ebay_seller_list()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
