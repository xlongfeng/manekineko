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
        'defer': fields.boolean('Allow deferred url fetching for create picture'),
        'description_included': fields.boolean('Description included'),
        'new_count': fields.integer('New List', readonly=True),
        'updated_count': fields.integer('Updated List', readonly=True),
        'state': fields.selection([
            ('option', 'option'),   # select ebay user option
            ('complete', 'complete')])
    }
    
    _defaults = {
        'defer': True,
        'description_included': False,
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
        ebay_item_variation = self.pool.get('ebay.item.variation')
        
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
        if this.description_included:
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
                        def _find_match_variation(variations, name_value_list, quantity_sold):
                            values = ''
                            if type(name_value_list) == list:
                                for name_value in name_value_list:
                                    values += name_value.Value
                            else:
                                values = name_value_list.Value
                            
                            for variation in variations:
                                specifices = variation.variation_specifics.replace(' ', '').replace('\n', '').replace('\r', '')
                                if specifices == values:
                                    variation.write(dict(quantity_sold=quantity_sold))
                                    break
                                
                        for variation in item.Variations.Variation:
                            _find_match_variation(
                                variation_ids,
                                variation.VariationSpecifics.NameValueList,
                                variation.SellingStatus.QuantitySold,
                            )
                    return status
                
                # find item sku first
                if sku:
                    data = sku.split('|')
                    if len(data) == 2:
                        id = data[0]
                        product_id = data[1]
                        if id.isdigit() and product_id.isdigit():
                            if ebay_item_obj.exists(cr, uid, int(id)):
                                vals = dict()
                                vals.update(update_item_status(item, ebay_item.variation_ids))
                                ebay_item = ebay_item_obj.browse(cr, uid, int(id), context=context)
                                ebay_item.write(vals)
                                updated_count += 1
                                continue
                            
                # find not sku item, base on item id
                _ids = ebay_item_obj.search(cr, uid, [('item_id', '=', item.ItemID)], context=context)
                if _ids:
                    id = _ids[0]
                    ebay_item = ebay_item_obj.browse(cr, uid, int(id), context=context)
                    vals = dict()
                    vals.update(update_item_status(item, ebay_item.variation_ids))
                    ebay_item.write(vals)
                    updated_count += 1
                    continue
                
                # new listing
                if selling_status.ListingStatus not in ('Active',):
                    continue
                
                vals = dict()
                vals['buy_it_now_price'] = item.BuyItNowPrice.value
                vals['condition_id'] = item.ConditionID if item.has_key('ConditionID') else None
                vals['currency'] = item.Currency
                if this.description_included:
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
                
                picture_index = 1
                eps_pictures = list()
                def get_eps_pictures(picture_index, picture_urls, specific_value = None):
                    _eps_pictures = list()
                    if type(picture_urls) != list:
                        picture_urls = [picture_urls]
                    for url in picture_urls:
                        vals = dict(
                            name='%03d' % picture_index,
                            full_url=url,
                            use_by_date=datetime.now() + timedelta(90),
                        )
                        if specific_value:
                            vals['variation_specific_value'] = specific_value
                        picture_index += 1
                        _eps_pictures.append(vals)
                    return picture_index, _eps_pictures
                
                if item.has_key('PictureDetails') and item.PictureDetails.has_key('PictureURL'):
                    picture_index, _eps_pictures = get_eps_pictures(picture_index, item.PictureDetails.PictureURL)
                    eps_pictures.extend(_eps_pictures)
                
                item_variation = list()
                if item.has_key('Variations'):
                    call_data = dict()
                    call_data['ItemID'] = item.ItemID
                    call_data['DetailLevel'] = 'ReturnAll'
                    call_data['OutputSelector'] =  [
                        'Item.Variations',
                    ]
                    error_msg = 'Get item: %s' % item.Title
                    reply = ebay_ebay_obj.call(cr, uid, user, 'GetItem', call_data, error_msg, context=context).response.reply
                    vals['variation_invalid'] = False
                    vals['variation'] = True
                    _variations = reply.Item.Variations
                    if _variations.has_key('Pictures'):
                        _pictures = _variations.Pictures
                        if _pictures.has_key('VariationSpecificPictureSet'):
                            picture_set = _pictures.VariationSpecificPictureSet
                            if type(picture_set) != list:
                                picture_set = [picture_set]
                            for picture in picture_set:
                                picture_index, _eps_pictures = get_eps_pictures(picture_index, picture.PictureURL, picture.VariationSpecificValue)
                                eps_pictures.extend(_eps_pictures)
                            
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
                    
                    vals['variation_specific_name'], vals['variation_specifics_set'] = get_specifices_set(_variations.VariationSpecificsSet.NameValueList)
                    
                    for _v in _variations.Variation:
                        variation_specific_name, variation_specifics=get_specifices_set(_v.VariationSpecifics.NameValueList)
                        item_variation.append(dict(
                            product_id=_v.SKU if _v.has_key('SKU') and _v.SKU.isdigit() else '',
                            quantity=_v.Quantity,
                            start_price=_v.StartPrice.value,
                            variation_specifics=variation_specifics,
                            quantity_sold=_v.SellingStatus.QuantitySold,
                        ))
                
                id = ebay_item_obj.create(cr, uid, vals, context=context)
                
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
                    
                for variation in item_variation:
                    variation['ebay_item_id'] = id
                    ebay_item_variation.create(cr, uid, variation, context=context)
                
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
        }

ebay_item_synchronize()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: