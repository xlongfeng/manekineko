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

class ebay_item_synchronize(osv.TransientModel):
    _name = 'ebay.item.synchronize'
    _description = 'eBay item synchronize '
    
    _columns = {
        'ebay_user_id': fields.many2one('ebay.user', 'eBay User', required=True, domain=[('ownership','=',True)]),
        'autocreate': fields.boolean('Auto Create not exist inventory'),
        'defer': fields.boolean('Deferred fetching pictures'),
        'new_count': fields.integer('New List', readonly=True),
        'updated_count': fields.integer('Updated List', readonly=True),
        'state': fields.selection([
            ('option', 'option'),   # select ebay user option
            ('complete', 'complete')])
    }
    
    _defaults = {
        'defer': True,
        'autocreate': False,
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
        if this.autocreate:
            output_selector.append('ItemArray.Item.Description')
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
                
                def update_item_status(item, variation_ids=None):
                    listing_details = item.ListingDetails
                    selling_status = item.SellingStatus
                    status = dict()
                    status['bid_count'] = selling_status.BidCount
                    status['end_time'] = listing_details.EndTime
                    status['hit_count'] = item.HitCount if item.has_key('HitCount') else 0
                    status['item_id'] = item.ItemID
                    status['quantity_sold'] = selling_status.QuantitySold
                    status['start_time'] = listing_details.StartTime
                    status['state'] = selling_status.ListingStatus
                    status['time_left'] = item.TimeLeft
                    status['update_date'] = fields.datetime.now()
                    status['watch_count'] = item.WatchCount if item.has_key('WatchCount') else 0
                    if variation_ids and item.has_key('Variations'):
                        for variation in item.Variations.Variation:
                            _id = variation.SKU if variation.has_key('SKU') and variation.SKU.isdigit() else ''
                            if _id:
                                record = ebay_item_obj.browse(cr, uid, int(_id), context=context)
                                if record.exists():
                                    record.write(dict(quantity_sold=variation.SellingStatus.QuantitySold))
                    
                    return status
                
                # find item sku first
                if sku and sku.isdigit() and ebay_item_obj.exists(cr, uid, int(sku), context=context):
                    print item.Title
                    ebay_item = ebay_item_obj.browse(cr, uid, int(sku), context=context)
                    ebay_item.write(update_item_status(item, ebay_item.child_ids))
                    updated_count += 1
                    continue
                            
                # find not sku item, base on item id, omit it
                if ebay_item_obj.search(cr, uid, [('item_id', '=', item.ItemID)], context=context):
                    updated_count += 1
                    continue
                
                # new listing
                if not this.autocreate or selling_status.ListingStatus not in ('Active',):
                    continue
                
                vals = dict()
                vals['buy_it_now_price'] = item.BuyItNowPrice.value
                vals['condition_id'] = item.ConditionID if item.has_key('ConditionID') else None
                vals['currency'] = item.Currency
                if this.autocreate:
                    description = item.Description
                    start_token = '<!-- DESCRIPTION START -->'
                    end_token = '<!-- DESCRIPTION END -->'
                    start = description.find(start_token)
                    end = description.find(end_token)
                    if start != -1 and end != -1:
                        description = description[start+len(start_token):end]
                    vals['description'] = description
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
                
                vals.update(update_item_status(item))
                
                vals['ebay_user_id'] = user.id
                
                def get_eps_pictures(picture_urls):
                    index = 1
                    _eps_pictures = list()
                    if type(picture_urls) != list:
                        picture_urls = [picture_urls]
                    for url in picture_urls:
                        vals = dict(
                            name='%03d' % index,
                            full_url=url,
                            use_by_date=datetime.now() + timedelta(90),
                        )
                        index += 1
                        _eps_pictures.append(vals)
                    return _eps_pictures
                
                eps_pictures = list()
                if item.has_key('PictureDetails') and item.PictureDetails.has_key('PictureURL'):
                    eps_pictures = get_eps_pictures(item.PictureDetails.PictureURL)
                
                def item_create(vals, eps_pictures=None):
                    id = ebay_item_obj.create(cr, uid, vals, context=context)
                    if eps_pictures:
                        for picture in eps_pictures:
                            picture['ebay_item_id'] = id
                            url = picture['full_url']
                            if this.defer:
                                picture['image'] = img_def
                                picture['dummy'] = True
                            else:
                                try:
                                    picture['image'] = base64.encodestring(urllib2.urlopen(url).read())
                                except:
                                    picture['image'] = img_def
                            ebay_eps_picture_obj.create(cr, uid, picture, context=context)
                    return id
                
                id = item_create(vals, eps_pictures)
                
                if item.has_key('Variations'):
                    call_data = dict()
                    call_data['ItemID'] = item.ItemID
                    call_data['DetailLevel'] = 'ReturnAll'
                    call_data['OutputSelector'] =  [
                        'Item.Variations',
                    ]
                    error_msg = 'Get item: %s' % item.Title
                    reply = ebay_ebay_obj.call(cr, uid, user, 'GetItem', call_data, error_msg, context=context).response.reply
                    vals = dict(
                        variation_invalid=False,
                        variation=True,
                    )
                    variations = reply.Item.Variations
                    variation_eps_pictures = dict()
                    if variations.has_key('Pictures'):
                        pictures = variations.Pictures
                        if pictures.has_key('VariationSpecificPictureSet'):
                            picture_set = pictures.VariationSpecificPictureSet
                            if type(picture_set) != list:
                                picture_set = [picture_set]
                            for picture in picture_set:
                                variation_eps_pictures[picture.VariationSpecificValue] = get_eps_pictures(picture.PictureURL)
                            
                    def get_specifices_set(name_value_list):
                        variation_specific_name = list()
                        variation_specifics_set = ''
                        if type(name_value_list) != list:
                            name_value_list = [name_value_list]
                        for name_value in name_value_list:
                            variation_specific_name.append(name_value.Name)
                            values = name_value.Value
                            if type(values) != list:
                                values = [values]
                            if variation_specifics_set:
                                variation_specifics_set = variation_specifics_set + '\n'
                            variation_specifics_set = variation_specifics_set + '|'.join(values)
                        return '|'.join(variation_specific_name), variation_specifics_set
                    
                    vals['variation_specific_name'], vals['variation_specifics_set'] = get_specifices_set(variations.VariationSpecificsSet.NameValueList)
                    # update item variation
                    ebay_item_obj.write(cr, uid, id, vals, context=context)
                    
                    for _v in variations.Variation:
                        def split_str(s, sep):
                            if not s:
                                return list()
                            if sep == '\n':
                                s_list = s.splitlines()
                            else:
                                s_list = s.split(sep)
                            d = list()
                            for l in s_list:
                                d.append(l.strip())
                            return d
                        
                        variation_specific_name, variation_specifics=get_specifices_set(_v.VariationSpecifics.NameValueList)
                        specific_values = split_str(variation_specifics, '\n')
                        vals = dict(
                            quantity=_v.Quantity,
                            start_price=_v.StartPrice.value,
                            name="[%s]" % ']['.join(specific_values),
                            variation_specifics_set=variation_specifics,
                            parent_id = id,
                            quantity_sold=_v.SellingStatus.QuantitySold,
                            state='Active',
                        )
                        
                        # create item child variation
                        if variation_eps_pictures.has_key(specific_values[0]):
                            item_create(vals, variation_eps_pictures[specific_values[0]])
                        else:
                            item_create(vals)
                
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
            'res_model': 'ebay.item.synchronize',
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
            'domain': "[('parent_id','=',False)]",
        }

ebay_item_synchronize()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: