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

import sys
import io
import base64
import uuid
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

_logger = logging.getLogger(__name__)

class ebay_details(osv.osv):
    _name = "ebay.details"
    _description = "eBay details"
    
    _columns = {
        'name': fields.char('Name', required=True),
        'site_id': fields.selection([
            ('0', 'US'),
            ('2', 'Canada',),
            ('3', 'UK'),
            ('15', 'Australia'),
            ('201', 'HongKong'),
        ], 'Site', required=True),
        'sandbox': fields.boolean('Sandbox'),
        # Category Feature
        'ebay_details': fields.text('eBay Details', readonly=True),
    }
    
    _defaults = {
        'name': 'ebay details',
        'site_id': '0',
        'sandbox': False
    }
    
    def action_update(self, cr, uid, ids, context=None):
        ebay_ebay_obj = self.pool.get('ebay.ebay')
        for details in self.browse(cr, uid, ids, context=context):
            user = ebay_ebay_obj.get_arbitrary_auth_user(cr, uid, details.sandbox)
            call_data = dict()
            error_msg = 'Get the ebay details list for %s site' % details.site_id
            resp = self.pool.get('ebay.ebay').call(cr, uid, user, 'GeteBayDetails', call_data, error_msg, context=context).response_content()
            details.write(dict(ebay_details=resp))
    
ebay_details()

class ebay_category(osv.osv):
    _name = "ebay.category"
    _description = "eBay category"
    
    _columns = {
        'name': fields.char('Name', required=True),
        'category_site_id': fields.selection([
            ('0', 'US'),
            ('2', 'Canada',),
            ('3', 'UK'),
            ('15', 'Australia'),
            ('201', 'HongKong'),
        ], 'Category Site', required=True),
        'sandbox': fields.boolean('Sandbox'),
        'category_id': fields.char('Category ID', size=10, required=True),
        # Category Feature
        'condition_enabled': fields.char('ConditionEnabled', readonly=True),
        'condition_values': fields.text('ConditionValues'),
        'free_gallery_plus_enabled': fields.boolean('FreeGalleryPlusEnabled', readonly=True),
        'free_picture_pack_enabled': fields.boolean('FreePicturePackEnabled', readonly=True),
        'handling_time_enabled': fields.boolean('HandlingTimeEnabled', readonly=True),
        'item_specifics_enabled': fields.char('ItemSpecificsEnabled', readonly=True),
        'variations_enabled': fields.boolean('VariationsEnabled', readonly=True),
        'category_feature': fields.text('Category Feature', readonly=True),
    }
    
    _defaults = {
        'category_site_id': '0',
        'sandbox': False
    }
    
    def action_update(self, cr, uid, ids, context=None):
        ebay_ebay_obj = self.pool.get('ebay.ebay')
        for category in self.browse(cr, uid, ids, context=context):
            user = ebay_ebay_obj.get_arbitrary_auth_user(cr, uid, category.sandbox)
            call_data=dict()
            call_data['CategoryParent'] = category.category_id
            call_data['CategorySiteID'] = category.category_site_id
            #call_data['ViewAllNodes'] = False
            error_msg = 'Get the category information for %s' % category.category_id
            #resp = ebay_ebay_obj.call(cr, uid, user, 'GetCategories', call_data, error_msg, context=context).response_dict()
            #ebay_ebay_obj.dump_resp(cr, uid, resp)
            
            call_data = dict()
            call_data['AllFeaturesForCategory'] = True
            call_data['CategoryID'] = category.category_id
            call_data['ViewAllNodes'] = True
            call_data['DetailLevel'] = 'ReturnAll'
            error_msg = 'Get the category features for %s' % category.category_id
            api = ebay_ebay_obj.call(cr, uid, user, 'GetCategoryFeatures', call_data, error_msg, context=context)
            resp_dict = api.response_dict()
            category_feature = resp_dict.Category
            vals = dict()
            vals['condition_enabled'] = category_feature.ConditionEnabled
            vals['condition_values'] = ebay_ebay_obj.format_pairs(cr, uid, category_feature.ConditionValues.Condition)
            vals['free_gallery_plus_enabled'] = category_feature.get('FreeGalleryPlusEnabled', False)
            vals['free_picture_pack_enabled'] = category_feature.get('FreePicturePackEnabled', False)
            vals['handling_time_enabled'] = category_feature.get('HandlingTimeEnabled', False)
            vals['item_specifics_enabled'] = category_feature.ItemSpecificsEnabled
            vals['variations_enabled'] = category_feature.get('VariationsEnabled', False)
            vals['category_feature'] = api.response_content()
            category.write(vals)
    
ebay_category()

class ebay_buyerrequirementdetails(osv.osv):
    _name = "ebay.buyerrequirementdetails"
    _description = "eBay buyer requirement details"
    
    _columns = {
        'name': fields.char('Name', required=True),
        'linked_paypal_account': fields.boolean('LinkedPayPalAccount'),
        # MaximumBuyerPolicyViolations
        'mbpv_count': fields.integer('Count'),
        'mbpv_period': fields.selection([
            ('Days_30', '30 days'),
            ('Days_180', '180 days'),
            ],'Period'),
        # MaximumItemRequirements
        'mir_maximum_item_count': fields.integer('MaximumItemCount'),
        'mir_minimum_feedback_score': fields.integer('MinimumFeedbackScore'),
        # MaximumUnpaidItemStrikesInfo
        'muisi_count': fields.integer('Count'),
        'muisi_period': fields.selection([
            ('Days_30', '30 days'),
            ('Days_180', '180 days'),
            ('Days_360', '360 days'),
            ],'Period'),
        'minimum_feedback_score': fields.integer('MinimumFeedbackScore'),
        'ship2registration_country': fields.boolean('ShipToRegistrationCountry'),
        # VerifiedUserRequirements
        'vur_minimum_feedback_score': fields.integer('MinimumFeedbackScore'),
        'vur_verified_user': fields.boolean('VerifiedUser'),
        'zero_feedback_score': fields.boolean('ZeroFeedbackScore'),
        'ebay_item_ids': fields.one2many('ebay.item', 'buyer_requirement_details_id', 'Item'),
    }
    
    _defaults = {
        'linked_paypal_account': False,
        'mbpv_count': 4,
        'mbpv_period': 'Days_180',
        'mir_maximum_item_count': 25,
        'mir_minimum_feedback_score': 5,
        'muisi_count': 2,
        'muisi_period': 'Days_30',
        'minimum_feedback_score': -1,
        'ship2registration_country': True,
        'vur_minimum_feedback_score': 5,
        'vur_verified_user': True,
        'zero_feedback_score': False,
    }
    
ebay_buyerrequirementdetails()
    
class ebay_conditiondescription(osv.osv):
    _name = "ebay.conditiondescription"
    _description = "eBay condition description"
    
    _columns = {
        'name': fields.char('Name', required=True),
        'description': fields.text('Description', size=1000, required=True),
        'ebay_item_ids': fields.one2many('ebay.item', 'condition_description_id', 'Item'),
    }
    
    _defaults = {
    }
    
ebay_conditiondescription()

class ebay_eps_picturesetmember(osv.osv):
    _name = "ebay.eps.picturesetmember"
    _description = "eBay EPS Picture"
    
    _columns = {
        'member_url': fields.char('URL'),
        'picture_height': fields.integer('Height'),
        'picture_width': fields.integer('Width'),
        'ebay_eps_picture_id': fields.many2one('ebay.eps.picture', 'EPS Picture', ondelete='cascade'),
    }
    
    _rec_name = 'member_url'

ebay_eps_picturesetmember()

class ebay_eps_picture(osv.osv):
    _name = "ebay.eps.picture"
    _description = "eBay EPS Picture"
    
    def _get_image(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.image)
        return result
    
    def _set_image(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'image': tools.image_resize_image_big(value)}, context=context)
    
    def _has_image(self, cr, uid, ids, name, args, context=None):
        result = {}
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = obj.image != False
        return result
    
    _columns = {
        'name': fields.char('Name', required=True),
        # image: all image fields are base64 encoded and PIL-supported
        'image': fields.binary("Image", required=True,
            help="This field holds the image used as avatar for this contact, limited to 1024x1024px"),
        'image_medium': fields.function(_get_image, fnct_inv=_set_image,
            string="Medium-sized image", type="binary", multi="_get_image",
            store={
                'ebay.eps.picture': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Medium-sized image of this contact. It is automatically "\
                 "resized as a 128x128px image, with aspect ratio preserved. "\
                 "Use this field in form views or some kanban views."),
        'image_small': fields.function(_get_image, fnct_inv=_set_image,
            string="Small-sized image", type="binary", multi="_get_image",
            store={
                'ebay.eps.picture': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Small-sized image of this contact. It is automatically "\
                 "resized as a 64x64px image, with aspect ratio preserved. "\
                 "Use this field anywhere a small image is required."),
        'has_image': fields.function(_has_image, type="boolean"),
        # SiteHostedPictureDetails
        'base_url': fields.char('BaseURL', readonly=True),
        'external_picture_url ': fields.char('ExternalPictureURL', readonly=True),
        'full_url': fields.char('FullURL', readonly=True),
        'picture_format': fields.char('PictureFormat', readonly=True),
        'picturesetmember_ids': fields.one2many('ebay.eps.picturesetmember', 'ebay_eps_picture_id', 'PictureSetMember', readonly=True),
        'use_by_date': fields.datetime('UseByDate', readonly=True),
        'variation_specific_value': fields.char('Variation Specific Value', size=40),
        'ebay_item_id': fields.many2one('ebay.item', 'Item', readonly=True, ondelete='cascade'),
    }
    
    _defaults = {
    }
    
    _order = 'name'
    
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if not ids:
            return True
        if 'image' in vals:
            vals['use_by_date'] = fields.datetime.now()
        return super(ebay_eps_picture, self).write(cr, uid, ids, vals, context=context)
    
ebay_eps_picture()

class ebay_returnpolicy(osv.osv):
    _name = "ebay.returnpolicy"
    _description = "eBay return policy"
    
    _columns = {
        'name': fields.char('Name', required=True),
        'description': fields.text('Description', size=5000),
        'refund_option': fields.char('RefundOption', required=True),
        'restocking_feevalue_option': fields.char('RestockingFeeValueOption'),
        'returns_accepted_option': fields.char('ReturnsAcceptedOption', required=True),
        'returns_within_option': fields.char('ReturnsWithinOption', required=True),
        'shipping_cost_paid_by_option': fields.char('ShippingCostPaidByOption', required=True),
        'warranty_duration_option': fields.char('WarrantyDurationOption'),
        'warranty_offered_option': fields.char('WarrantyOfferedOption'),
        'warranty_type_option': fields.char('WarrantyTypeOption'),
        'ebay_item_ids': fields.one2many('ebay.item', 'return_policy_id', 'Item'),
    }

    _defaults = {
    }
    
ebay_returnpolicy()

class ebay_shippingdetails(osv.osv):
    _name = "ebay.shippingdetails"
    _description = "eBay shipping details"
    
    _columns = {
        'name': fields.char('Name', required=True),
        'exclude_ship_to_location': fields.text('Exclude Ship To Location'),
        # InternationalShippingServiceOption
        # Shipping costs and options related to an international shipping service.
        'isso_shipping_service': fields.char('Shipping Service', required=True),
        'isso_shipping_service_additional_cost': fields.float('Additional Cost'),
        'isso_shipping_service_cost': fields.float('Cost'),
        'isso_shipping_service_priority': fields.integer('ShippingServicePriority'),
        # ShippingServiceOptions
        # Shipping costs and options related to domestic shipping services offered by the seller.
        # Flat and calculated shipping.
        'sso_free_shipping': fields.boolean('Free Shipping'),
        'sso_shipping_service': fields.char('Shipping Service', required=True),
        'sso_shipping_service_additional_Cost': fields.float('Additional Cost'),
        'sso_shipping_service_cost': fields.float('Cost'),
        'sso_shipping_service_priority': fields.integer('ShippingServicePriority'),
        'shipping_type': fields.selection([
            ('Calculated', 'Calculated'),
            ('CalculatedDomesticFlatInternational', 'CalculatedDomesticFlatInternational'),
            ('CustomCode', 'CustomCode'),
            ('Flat', 'Flat'),
            ('FlatDomesticCalculatedInternational', 'FlatDomesticCalculatedInternational'),
            ('FreightFlat', 'FreightFlat'),
            ('NotSpecified', 'NotSpecified'),
        ], 'ShippingType', readonly=True),
        'ebay_item_ids': fields.one2many('ebay.item', 'shipping_details_id', 'Item'),
    }
    
    _defaults = {
        'isso_shipping_service': 'OtherInternational',
        'isso_shipping_service_additional_cost': 0.0,
        'isso_shipping_service_cost': 0.0,
        'isso_shipping_service_priority': 1,
        'sso_free_shipping': True,
        'sso_shipping_service': 'EconomyShippingFromOutsideUS',
        'sso_shipping_service_additional_Cost': 0.0,
        'sso_shipping_service_cost': 0.0,
        'sso_shipping_service_priority': 1,
        'shipping_type': 'Flat',
    }
    
    def on_change_sso_free_shipping(self, cr, uid, id, sso_free_shipping, context=None):
        if sso_free_shipping:
            return {
                'value': {
                    'sso_shipping_service_cost': 0.0,
                    'sso_shipping_service_additional_Cost': 0.0,
                }
            }
        else:
            return {
                'value': {
                }
            }
    
ebay_shippingdetails()

class ebay_item_variation(osv.osv):
    _name = "ebay.item.variation"
    _description = "eBay item variation"
    
    _columns = {
        'quantity': fields.integer('Quantity', required=True),
        'product_id': fields.many2one('product.product', 'SKU', ondelete='no action'),
        'start_price': fields.float('StartPrice', required=True),
        'variation_specifics': fields.text('VariationSpecificsSet'),
        'quantity_sold': fields.integer('Quantity Sold', readonly=True),
        'ebay_item_id': fields.many2one('ebay.item', 'Item', ondelete='cascade'),
    }
    
    _defaults = {
        'start_price': 9.99
    }
    
ebay_item_variation()

class ebay_item(osv.osv):
    _name = "ebay.item"
    _description = "eBay item"
    
    def _get_item_view_url(self, cr, uid, ids, field_name, arg, context):
        if context is None:
            context = {}
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            if record.item_id:
                if record.ebay_user_id.sandbox:
                    res[record.id] = "http://cgi.sandbox.ebay.com/ws/eBayISAPI.dll?ViewItem&item=%s" % record.item_id
                else:
                    res[record.id] = "http://cgi.ebay.com/ws/eBayISAPI.dll?ViewItem&item=%s" % record.item_id
        return res
    
    _columns = {
        #'auto_pay': fields.boolean('AutoPay'),
        'buyer_requirement_details_id': fields.many2one('ebay.buyerrequirementdetails', 'Buyer Requirement', ondelete='set null'),
        'buy_it_now_price': fields.float('BuyItNowPrice'),
        'condition_description_id': fields.many2one('ebay.conditiondescription', 'Condition Description', ondelete='set null'),
        'condition_id': fields.integer('Condition ID'),
        'country': fields.char('Country', size=2),
        'cross_border_trade': fields.char('CrossBorderTrade'),
        'currency': fields.char('Currency', size=3),
        'description': fields.html('Description'),
        'disable_buyer_requirements': fields.boolean('DisableBuyerRequirements'),
        'dispatch_time_max': fields.integer('DispatchTimeMax'),
        'hit_counter': fields.selection([
            ('BasicStyle', 'BasicStyle'),
            ('CustomCode', 'CustomCode'),
            ('GreenLED', 'GreenLED'),
            ('Hidden', 'Hidden'),
            ('HiddenStyle', 'HiddenStyle'),
            ('HonestyStyle', 'HonestyStyle'),
            ('NoHitCounter', 'NoHitCounter'),
            ('RetroStyle', 'RetroStyle'),
        ], 'HitCounter'),
        'include_recommendations': fields.boolean('IncludeRecommendations'),
        'item_specifics': fields.text('ItemSpecifics', help="""
            For example:
            Name1=Value1
            Name2=Value2
            Name3=Value3
        """),
        'listing_duration': fields.char('Duration', size=8),
        'listing_type': fields.selection([
            #('AdType', 'AdType'),
            ('Chinese', 'Auction'),
            #('CustomCode', 'CustomCode'),
            ('FixedPriceItem', 'Fixed Price'),
            #('Half', 'Half'),
            #('LeadGeneration', 'LeadGeneration'),
        ], 'Format', required=True),
        'location': fields.char('Location'),
        'out_of_stock_control': fields.boolean('OutOfStockControl'),
        'payment_methods': fields.char('PaymentMethods'),
        'paypal_email_address': fields.char('PayPalEmailAddress'),
        'payment_methods': fields.char('PaymentMethods'),
        #PictureDetails
        'eps_picture_ids': fields.one2many('ebay.eps.picture', 'ebay_item_id', 'Picture'),
        'postal_code': fields.char('PostalCode'),
        'primary_category_id': fields.many2one('ebay.category', 'Category', required=True, ondelete='set null'),
        'quantity': fields.integer('Quantity'),
        'return_policy_id': fields.many2one('ebay.returnpolicy', 'Return Policy', required=True, ondelete='set null'),
        'schedule_time': fields.datetime('ScheduleTime'),
        'secondary_category_id': fields.many2one('ebay.category', '2nd Category', ondelete='set null'),
        'shipping_details_id': fields.many2one('ebay.shippingdetails', 'Shipping Details', required=True, ondelete='set null'),
        'shipping_terms_in_description': fields.boolean('ShippingTermsInDescription'),
        'site': fields.char('Site', size=16),
        # SKU
        'product_id': fields.many2one('product.product', 'Product', ondelete='set null'),
        'start_price': fields.float('StartPrice', required=True),
        # Storefront
        'store_category2id': fields.integer('2nd Store Category'),
        'store_category2name': fields.char('2nd Store Category'),
        'store_category_id': fields.integer('Store Category'),
        'store_category_name': fields.char('Store Category'),
        'subtitle': fields.char('SubTitle', size=55),
        'name': fields.char('Title', size=80, required=True, select=True),
        'uuid': fields.char('UUID', size=32),
        # Variations
        'variation_invalid': fields.boolean('Variation Invalid'),
        'variation': fields.boolean('Variation'),
        'variation_specific_name': fields.char('VariationSpecificName', size=40),
        'variations_pictures': fields.text('VariationsPictures'),
        'variation_specifics_set': fields.text('VariationSpecificsSet'),
        'variation_ids': fields.one2many('ebay.item.variation', 'ebay_item_id', 'Variantions'),
        # Item Status ------------
        'bid_count': fields.integer('Bit Count', readonly=True),
        'end_time': fields.datetime('End Time', readonly=True),
        'hit_count': fields.integer('Hit Count', readonly=True),
        'item_id': fields.char('Item ID', size=38, readonly=True),
        'quantity_sold': fields.integer('Quantity Sold', readonly=True),
        'start_time': fields.datetime('Start Time', readonly=True),
        'state': fields.selection([
            ('Draft', 'Draft'),
            ('Active', 'Active'),
            ('Completed', 'Completed'),
            ('Ended', 'Ended'),
        ], 'Listing Status', readonly=True),
        'time_left': fields.char('Time Left', readonly=True),
        'view_item_url': fields.function(_get_item_view_url, type='char', method="True", string='View Item'),
        'watch_count': fields.integer('Watch Count', readonly=True),
        'response': fields.text('Response', readonly=True),
        # Additional Info
        'description_tmpl_id': fields.many2one('ebay.item.description.template', 'Template', ondelete='set null'),
        'site': fields.selection([
            ('US', 'US'),
            ('Canada', 'Canada',),
            ('UK', 'UK'),
            ('Australia', 'Australia'),
            ('HongKong', 'HongKong'),
        ], 'Site', required=True),
        'ebay_user_id': fields.many2one('ebay.user', 'Account', required=True, domain=[('ownership','=',True)], ondelete='set null'),
    }
    
    _defaults = {
        'buy_it_now_price': 19.99,
        'condition_id': 1000,
        'cross_border_trade': 'North America',
        'country': 'CN',
        'currency': 'USD',
        'disable_buyer_requirements': False,
        'dispatch_time_max': 2,
        'hit_counter': 'HiddenStyle',
        'include_recommendations': True,
        'listing_duration': 'GTC',
        'listing_type': 'FixedPriceItem',
        'location': 'ShenZhen',
        'quantity': 1,
        'start_price': 9.99,
        'state': 'Draft',
        'site': 'US',
        'uuid': lambda self, cr, uid, context: uuid.uuid1().hex,
    }
    
    def on_change_primary_category_id(self, cr, uid, id, primary_category_id, listing_type, context=None):
        if not primary_category_id:
            return False
        value = dict()
        variation_invalid = False
        category = self.pool.get('ebay.category').browse(cr, uid, primary_category_id, context=context)
        if listing_type == 'Chinese':
            value['quantity'] = 1
            value['listing_duration'] = 'Days_7'
        else:
            value['quantity'] = 99
            value['listing_duration'] = 'GTC'
        if listing_type == 'Chinese' or not category.variations_enabled:
            value['variation_invalid'] = True
        else:
            value['variation_invalid'] = False
        return {
            'value': value
        }
    
    def on_change_listing_type(self, cr, uid, id, primary_category_id, listing_type, context=None):
        return self.on_change_primary_category_id(cr, uid, id, primary_category_id, listing_type, context=context)
    
    def copy(self, cr, uid, record_id, default=None, context=None):
        if default is None:
            default = {}

        default.update({
            'item_id': '',
            'state': 'Draft',
            'uuid': uuid.uuid1().hex,
        })

        return super(ebay_item, self).copy(cr, uid, record_id, default, context)
    
    def upload_pictures(self, cr, uid, user, eps_pictures, context=None):
        if not eps_pictures:
            return list()
        
        ebay_eps_picturesetmember = self.pool.get('ebay.eps.picturesetmember')
        # TODO
        time_now_pdt = datetime.now()
        for picture in eps_pictures:
            if not picture.use_by_date or (parser.parse(picture.use_by_date) - time_now_pdt).days < 2:
                image = io.BytesIO(base64.b64decode(picture.image))
                call_data = dict()
                call_data['PictureSystemVersion'] = 2
                call_data['PictureUploadPolicy'] = 'Add'
                error_msg = 'Upload image %s' % picture.name
                resp_dict = self.pool.get('ebay.ebay').call(cr, uid, user,
                    'UploadSiteHostedPictures', call_data, error_msg, files=dict(image=image), context=context).response_dict()
                site_hosted_picture_details = resp_dict.SiteHostedPictureDetails
                vals = dict()
                vals['base_url'] = site_hosted_picture_details.BaseURL
                vals['external_picture_url'] = site_hosted_picture_details.get('ExternalPictureURL', {}).get('value', '')
                vals['full_url'] = site_hosted_picture_details.FullURL
                vals['picture_format'] = site_hosted_picture_details.PictureFormat
                vals['use_by_date'] = site_hosted_picture_details.UseByDate
                picture.write(vals)
                picture_set_member = site_hosted_picture_details.PictureSetMember
                cr.execute('delete from ebay_eps_picturesetmember \
                        where ebay_eps_picture_id=%s', (picture.id,))
                for picture_set in picture_set_member:
                    vals = dict()
                    vals['member_url'] = picture_set.MemberURL
                    vals['picture_height'] = picture_set.PictureHeight
                    vals['picture_width'] = picture_set.PictureWidth
                    vals['ebay_eps_picture_id'] = picture.id
                    ebay_eps_picturesetmember.create(cr, uid, vals, context=context)
                    
        return eps_pictures
                    
    def item_create(self, cr, uid, item, context=None):
        user = item.ebay_user_id
        auction = item.listing_type == 'Chinese'
        
        item_dict = {
            'Item': {
                'CategoryMappingAllowed': 'true',
                "ConditionID": item.condition_id,
                'Country': user.country,
                'Currency': item.currency,
                'Description': '<![CDATA[' + item.description + ']]>',
                'DispatchTimeMax': item.dispatch_time_max,
                'ListingDuration': item.listing_duration,
                'Location': user.location,
                'PaymentMethods': 'PayPal',
                'PayPalEmailAddress': user.paypal_email_address,
                'Quantity': item.quantity,
                'Site': item.site,
                'SKU': item.id,
                'StartPrice': item.start_price,
                'Title': '<![CDATA[' + item.name + ']]>',
                #'UUID': item.uuid,
            }
        }
        
        if auction:
            if item.buy_it_now_price:
                item_dict['Item']['BuyItNowPrice'] = item.buy_it_now_price
            
        if item.primary_category_id.condition_enabled:
            item_dict['Item']['PrimaryCategory'] = dict(CategoryID=item.primary_category_id.category_id)
        
        picture_url = list()
        for picture in self.upload_pictures(cr, uid, user, item.eps_picture_ids, context=context):
            if picture.full_url:
                picture_url.append(picture.full_url)
        else:
            if len(picture_url) == 1:
                item_dict['Item']['PictureDetails'] = dict(PictureURL=picture_url[0])
            elif len(picture_url) > 1:
                item_dict['Item']['PictureDetails'] = dict(PictureURL=picture_url)
                
        if item.buyer_requirement_details_id:
            brd = item.buyer_requirement_details_id
            buyer_requirement_details = dict(
                LinkedPayPalAccount="true" if brd.linked_paypal_account else "false",
                MinimumFeedbackScore=brd.minimum_feedback_score,
                ShipToRegistrationCountry="true" if brd.ship2registration_country else "false",
            )
            
            buyer_requirement_details['MaximumBuyerPolicyViolations'] = dict(
                Count=brd.mbpv_count,
                Period=brd.mbpv_period,
            )
            
            buyer_requirement_details['MaximumItemRequirements'] = dict(
                MaximumItemCount=brd.mir_maximum_item_count,
                MinimumFeedbackScore=brd.mir_minimum_feedback_score,
            )
            
            buyer_requirement_details['MaximumUnpaidItemStrikesInfo'] = dict(
                Count=brd.muisi_count,
                Period=brd.muisi_period,
            )
            '''
            buyer_requirement_details['VerifiedUserRequirements'] = dict(
                MinimumFeedbackScore=brd.vur_minimum_feedback_score,
                VerifiedUser=brd.vur_verified_user,
            )
            '''
            
            item_dict['Item']['BuyerRequirementDetails'] = buyer_requirement_details
            
        if item.return_policy_id:
            rp = item.return_policy_id
            return_policy = dict(
                RefundOption=rp.refund_option,
                ReturnsAcceptedOption=rp.returns_accepted_option,
                ReturnsWithinOption=rp.returns_within_option,
                ShippingCostPaidByOption=rp.shipping_cost_paid_by_option,
            )
            if rp.description:
                return_policy['description'] = '<![CDATA[' + rp.description + ']]>'
            item_dict['Item']['ReturnPolicy'] = return_policy
        
        if item.shipping_details_id:
            sd = item.shipping_details_id
            shipping_details = dict()
            shipping_details['InternationalShippingServiceOption'] = dict(
                ShippingService=sd.isso_shipping_service,
                ShippingServiceAdditionalCost=sd.sso_shipping_service_additional_Cost,
                ShippingServiceCost=sd.isso_shipping_service_cost,
                ShippingServicePriority=sd.isso_shipping_service_priority,
                ShipToLocation='Worldwide'
            )
            
            shipping_details['ShippingServiceOptions'] = dict(
                ShippingService=sd.sso_shipping_service,
                ShippingServicePriority=sd.sso_shipping_service_priority,
            )
            if sd.sso_free_shipping:
                shipping_details['ShippingServiceOptions']['FreeShipping'] = "true"
            else:
                shipping_details['ShippingServiceOptions']['ShippingServiceAdditionalCost'] = sd.sso_shipping_service_additional_Cost
                shipping_details['ShippingServiceOptions']['ShippingServiceCost'] = sd.sso_shipping_service_cost

            shipping_details['ShippingType'] = sd.shipping_type
            
            item_dict['Item']['ShippingDetails'] = shipping_details
        
        return item_dict, auction
    
    def action_verify(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids, context=context):
            user = item.ebay_user_id
            item_dict, auction = self.item_create(cr, uid, item, context=context)
            ebay_ebay_obj = self.pool.get('ebay.ebay')
            error_msg = 'Verify add item: %s' % item.name
            call_name = "VerifyAddItem" if auction else "VerifyAddFixedPriceItem"
            api = ebay_ebay_obj.call(cr, uid, user, call_name, item_dict, error_msg, context=context)
            item.write(dict(response=api.response.json()))
            
    def action_upload(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids, context=context):
            user = item.ebay_user_id
            item_dict, auction = self.item_create(cr, uid, item, context=context)
            ebay_ebay_obj = self.pool.get('ebay.ebay')
            error_msg = 'Add item: %s' % item.name
            call_name = "AddItem" if auction else "AddFixedPriceItem"
            api = ebay_ebay_obj.call(cr, uid, user, call_name, item_dict, error_msg, context=context)
            ebay_ebay_obj.dump_resp(cr, uid, api, context=context)
            vals = dict()
            vals['end_time'] = api.response.reply.EndTime
            vals['item_id'] = api.response.reply.ItemID
            vals['start_time'] = api.response.reply.StartTime
            vals['state'] = 'Active'
            vals['response'] = api.response.json()
            item.write(vals)
            
    def action_revise(self, cr, uid, ids, context=None):
        pass
        
    def action_synchronize(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids, context=context):
            user = item.ebay_user_id
            call_data = dict()
            call_data['IncludeWatchCount'] = 'true'
            call_data['ItemID'] = item.item_id
            call_data['DetailLevel'] = 'ReturnAll'
            call_data['OutputSelector'] =  [
                'Item.HitCount',
                'Item.ListingDetails',
                'Item.SellingStatus',
                'Item.TimeLeft',
                'Item.WatchCount',
            ]
            error_msg = 'Get item: %s' % item.name
            ebay_ebay_obj = self.pool.get('ebay.ebay')
            api = ebay_ebay_obj.call(cr, uid, user, 'GetItem', call_data, error_msg, context=context)
            reply = api.response.reply
            ebay_ebay_obj.dump_resp(cr, uid, api, context=context)
            vals = dict()
            vals['hit_count'] = reply.Item.HitCount
            listing_details = reply.Item.ListingDetails
            vals['end_time'] = listing_details.EndTime
            vals['start_time'] = listing_details.StartTime
            selling_status = reply.Item.SellingStatus
            vals['bid_count'] = selling_status.BidCount
            vals['quantity_sold'] = selling_status.QuantitySold
            vals['state'] = selling_status.ListingStatus
            vals['time_left'] = reply.Item.TimeLeft
            vals['watch_count'] = reply.Item.WatchCount
            item.write(vals)
            
    def action_end_listing(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids, context=context):
            user = item.ebay_user_id
            auction = item.listing_type == 'Chinese'
            error_msg = 'End item: %s' % item.name
            call_name = "EndItem" if auction else "EndFixedPriceItem"
            call_data = dict()
            call_data['EndingReason'] = 'NotAvailable'
            call_data['ItemID'] = item.item_id
            ebay_ebay_obj = self.pool.get('ebay.ebay')
            api = ebay_ebay_obj.call(cr, uid, user, call_name, call_data, error_msg, context=context)
            vals = dict()
            vals['end_time'] = api.response.reply.EndTime
            vals['state'] = 'Ended'
            item.write(vals)
            
ebay_item()

class ebay_item_description_template(osv.osv):
    _name = "ebay.item.description.template"
    _description = "eBay item description template"
    
    _columns = {
        'name': fields.char('Name', required=True, select=True),
        'template': fields.html('Template'),
        'ebay_item_ids': fields.one2many('ebay.item', 'description_tmpl_id', 'Item'),
    }
    
    _defaults = {
    }
    
ebay_item_description_template()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
