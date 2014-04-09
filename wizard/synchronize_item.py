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

import os
import sys
import base64
import urllib2
import logging
from datetime import datetime, timedelta, tzinfo
import dateutil.parser as parser
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time
import pytz

import openerp
from openerp import tools
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class ebay_synchronize_item(osv.TransientModel):
    _name = 'ebay.synchronize.item'
    _description = 'eBay synchronize item'
    
    _columns = {
        'ebay_user_id': fields.many2one('ebay.user', 'Account', required=True, domain=[('ownership','=',True)]),
        'new_count': fields.integer('New List', readonly=True),
        'updated_count': fields.integer('Updated List', readonly=True),
        'state': fields.selection([
            ('option', 'option'),   # select ebay user option
            ('complete', 'complete')])
    }
    
    _defaults = {
        'state': 'option',
    }
    
    def action_sync(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        this = self.browse(cr, uid, ids)[0]
        new_count = 0
        updated_count = 0
        
        user = this.ebay_user_id
        
        ebay_ebay_obj = self.pool.get('ebay.ebay')
        ebay_item_obj = self.pool.get('ebay.item')
        ebay_category_obj = self.pool.get('ebay.category')
        ebay_eps_picture_obj = self.pool.get('ebay.eps.picture')
        
        img_path = openerp.modules.get_module_resource('ebay', 'static/src/img', 'icon.png')
        img_file = open(img_path, 'rb')
        img_def = base64.encodestring(img_file.read())
        
        output_selector = [
                'HasMoreItems',
                'ItemArray.Item.BuyItNowPrice',
                'ItemArray.Item.ConditionID',
                'ItemArray.Item.Currency',
                'ItemArray.Item.ItemID',
                'ItemArray.Item.ListingDetails',
                'ItemArray.Item.ListingDuration',
                'ItemArray.Item.ListingType',
                'ItemArray.Item.PictureDetails',
                'ItemArray.Item.PrimaryCategory',
                'ItemArray.Item.Quantity',
                'ItemArray.Item.SellingStatus',
                'ItemArray.Item.StartPrice',
                'ItemArray.Item.Site',
                'ItemArray.Item.SKU',
                'ItemArray.Item.TimeLeft',
                'ItemArray.Item.Title',
                'ItemArray.Item.Variations',
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
            call_data['IncludeVariations'] = 'true'
            call_data['IncludeWatchCount'] = 'true'
            call_data['Pagination'] = {
                'EntriesPerPage': entries_per_page,
                'PageNumber': page_number,
            }
            call_data['DetailLevel'] = 'ReturnAll'
            call_data['OutputSelector'] = output_selector
            error_msg = 'Get the seller list for the specified user %s' % user.name
            reply = ebay_ebay_obj.call(cr, uid, user, 'GetSellerList', call_data, error_msg, context=context).response.reply
            has_more_items = reply.HasMoreItems == 'true'
            items = reply.ItemArray.Item
            if type(items) != list:
                items = [items]
            for item in items:
                _logger.debug("Synchronize item: %s" % item.Title)
                sku = item.SKU if item.has_key('SKU') else ''
                listing_details = item.ListingDetails
                selling_status = item.SellingStatus
                
                # find item sku first
                if sku:
                    data = sku.split('|')
                    if len(data) == 2:
                        id = data[0]
                        product_id = data[1]
                        if item_id.isdigit() and id.isdigit():
                            ebay_item = ebay_item_obj.browse(cr, uid, int(id), context=context)
                            if ebay_item.id:
                                # update listing
                                updated_count += 1
                                continue
                            
                # find not sku item, base on item id
                _ids = ebay_item_obj.search(cr, uid, [('item_id', '=', item.ItemID)], context=context)
                if _ids:
                    id = _ids[0]
                    ebay_item = ebay_item_obj.browse(cr, uid, int(id), context=context)
                    # update listing
                    updated_count += 1
                    continue
                
                # new listing
                if selling_status.ListingStatus not in ('Active',):
                    continue
                
                vals = dict()
                vals['buy_it_now_price'] = item.BuyItNowPrice.value
                vals['condition_id'] = item.ConditionID if item.has_key('ConditionID') else None
                vals['currency'] = item.Currency
                vals['listing_duration'] = item.ListingDuration
                vals['listing_type'] = item.ListingType
                
                category_id = item.PrimaryCategory.CategoryID
                category_name = item.PrimaryCategory.CategoryName
                primary_category_id = ebay_category_obj.search_category(
                    cr, uid, category_id, category_name, user.sandbox, context=context)
                vals['primary_category_id'] = primary_category_id
                
                vals['quantity'] = item.Quantity
                vals['start_price'] = item.StartPrice.value
                vals['name'] = item.Title
                
                # Item Status ------------
                vals['bid_count'] = selling_status.BidCount
                vals['end_time'] = listing_details.EndTime
                vals['hit_count'] = item.HitCount if item.has_key('HitCount') else 0
                vals['item_id'] = item.ItemID
                vals['quantity_sold'] = selling_status.QuantitySold
                vals['start_time'] = listing_details.StartTime
                vals['state'] = selling_status.ListingStatus
                vals['time_left'] = item.TimeLeft
                vals['watch_count'] = item.WatchCount if item.has_key('WatchCount') else 0
                
                vals['ebay_user_id'] = user.id
                
                if item.has_key('PictureDetails'):
                    picture_details = item.PictureDetails
                
                id = ebay_item_obj.create(cr, uid, vals, context=context)
                
                # PictureDetails
                picture_index = 0
                if item.has_key('PictureDetails') and item.PictureDetails.has_key('PictureURL'):
                    picture_urls = item.PictureDetails.PictureURL
                    if type(picture_urls) != list:
                        picture_urls = [picture_urls]
                    for url in picture_urls:
                        vals = dict(
                            name=str(picture_index),
                            full_url=url,
                            use_by_date = fields.datetime.now(),
                            ebay_item_id = id,
                        )
                        try:
                            vals['image'] = base64.encodestring(urllib2.urlopen(url).read())
                        except:
                            vals['image'] = img_def
                        picture_index += 1
                        ebay_eps_picture_obj.create(cr, uid, vals, context=context)
                
                # Variations
                
                new_count += 1
            page_number = page_number + 1
        
        vals = dict(
            new_count=new_count,
            updated_count=updated_count,
            state='complete',
        )
        self.write(cr, uid, ids, vals, context=context)
        
        return {
            'name': "Synchronize",
            'type': 'ir.actions.act_window',
            'res_model': 'ebay.synchronize.item',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
    
    def action_close(self, cr, uid, ids, context=None):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Inventory',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'ebay.item',
        }

ebay_synchronize_item()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: