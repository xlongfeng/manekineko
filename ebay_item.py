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

class ebay_epspicture(osv.osv):
    _name = "ebay.epspicture"
    _description = "eBay EPS Picture"
    
    _columns = {
        'name': fields.char('Name', required=True),
        # SiteHostedPictureDetails
        'ebay_item_id': fields.many2one('ebay.item', 'Item', ondelete='cascade'),
        'variation_specific_value': fields.char('VariationSpecificValue', size=40),
    }
    
    _defaults = {
    }
    
ebay_epspicture()

class ebay_returnpolicy(osv.osv):
    _name = "ebay.returnpolicy"
    _description = "eBay return policy"
    
    _columns = {
        'name': fields.char('Name', required=True),
        'description': fields.text('Description', size=5000),
        'refund_option': fields.char('RefundOption'),
        'restocking_feevalue_option': fields.char('RestockingFeeValueOption'),
        'returns_accepted_option': fields.char('ReturnsAcceptedOption', required=True),
        'returns_within_option': fields.char('ReturnsWithinOption'),
        'shipping_cost_paid_by_option': fields.char('ShippingCostPaidByOption'),
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
        'isso_shipping_service_priority': 1,
        'sso_free_shipping': True,
        'sso_shipping_service': 'EconomyShippingFromOutsideUS',
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
        'ebay_item_id': fields.many2one('ebay.item', 'Item', ondelete='cascade'),
    }
    
    _defaults = {
        'start_price': 9.99
    }
    
ebay_item_variation()

class ebay_item(osv.osv):
    _name = "ebay.item"
    _description = "eBay item"
    
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
        'eps_picture_ids': fields.one2many('ebay.epspicture', 'ebay_item_id', 'Pictures'),
        'postal_code': fields.char('PostalCode'),
        'primary_category_id': fields.many2one('ebay.category', 'Category', required=True, ondelete='set null'),
        'quantity': fields.integer('Quantity'),
        'return_policy_id': fields.many2one('ebay.returnpolicy', 'Return Policy', ondelete='set null'),
        'schedule_time': fields.datetime('ScheduleTime'),
        'secondary_category_id': fields.many2one('ebay.category', '2nd Category', ondelete='set null'),
        'shipping_details_id': fields.many2one('ebay.shippingdetails', 'Shipping Details', ondelete='set null'),
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
        # Variations
        'variation_invalid': fields.boolean('Variation Invalid'),
        'variation': fields.boolean('Variation'),
        'variation_specific_name': fields.char('VariationSpecificName', size=40),
        'variations_pictures': fields.text('VariationsPictures'),
        'variation_specifics_set': fields.text('VariationSpecificsSet'),
        'variation_ids': fields.one2many('ebay.item.variation', 'ebay_item_id', 'Variantions'),
        # Additional Info
        'description_tmpl_id': fields.many2one('ebay.item.description.template', 'Template', ondelete='set null'),
        'site_id': fields.selection([
            ('0', 'US'),
            ('2', 'Canada',),
            ('3', 'UK'),
            ('15', 'Australia'),
            ('201', 'HongKong'),
        ], 'Site', required=True),
        'ebay_user_id': fields.many2one('ebay.user', 'Account', required=True, domain=[('ownership','=',True)], ondelete='set null'),
    }
    
    _defaults = {
        'buy_it_now_price': 19.99,
        'condition_id': 1000,
        'cross_border_trade': 'North America',
        'disable_buyer_requirements': False,
        'dispatch_time_max': 2,
        'hit_counter': 'HiddenStyle',
        'include_recommendations': True,
        'listing_duration': 'GTC',
        'listing_type': 'FixedPriceItem',
        'quantity': 1,
        'start_price': 9.99,
        'site_id': '0',
    }
    
    def on_change_primary_category_id(self, cr, uid, id, primary_category_id, listing_type, context=None):
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
