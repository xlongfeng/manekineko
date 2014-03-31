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

class ebay_category(osv.osv):
    _name = "ebay.category"
    _description = "eBay category"
    
    _columns = {
        'name': fields.char('Name', required=True),
        'auto_pay_enabled': fields.boolean('AutoPayEnabled', readonly=True),
        'b2bvat_enabled': fields.boolean('B2BVATEnabled', readonly=True),
        'best_offer_enabled': fields.boolean('BestOfferEnabled', readonly=True),
        'category_id': fields.char('CategoryID', size=10, required=True),
        'category_level': fields.integer('CategoryLevel', readonly=True),
        'category_name': fields.char('CategoryName', size=30, readonly=True),
        'category_parent_id': fields.char('CategoryParentID', size=10, readonly=True),
        'expired': fields.boolean('Expired', readonly=True),
        'intl_autos_fixed_cat': fields.boolean('IntlAutosFixedCat', readonly=True),
        'Leaf_Category': fields.boolean('LeafCategory', readonly=True),
        'lsd': fields.boolean('LSD', readonly=True),
        'orpa': fields.boolean('ORPA', readonly=True),
        'orra': fields.boolean('ORRA', readonly=True),
    }
    
    _defaults = {
    }
    
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
        'zero_feedback_score': True,
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
        'refund_option': fields.char('RefundOption', required=True),
        'restocking_feevalue_option': fields.char('RestockingFeeValueOption', required=True),
        'returns_accepted_option': fields.char('ReturnsAcceptedOption', required=True),
        'returns_within_option': fields.char('ReturnsWithinOption', required=True),
        'shipping_cost_paid_by_option': fields.char('ShippingCostPaidByOption', required=True),
        'warranty_duration_option': fields.char('WarrantyDurationOption', required=True),
        'warranty_offered_option': fields.char('WarrantyOfferedOption', required=True),
        'warranty_type_option': fields.char('WarrantyTypeOption', required=True),
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
        # InternationalShippingServiceOption
        # Shipping costs and options related to an international shipping service.
        'isso_shipping_service': fields.char('ShippingService', required=True),
        'isso_shipping_service_additional_cost': fields.float('ShippingServiceAdditionalCost'),
        'isso_shipping_service_cost': fields.float('ShippingServiceCost'),
        'isso_shipping_service_priority': fields.integer('ShippingServicePriority'),
        # ShippingServiceOptions
        # Shipping costs and options related to domestic shipping services offered by the seller.
        # Flat and calculated shipping.
        'sso_free_shipping': fields.boolean('FreeShipping', required=True),
        'sso_shipping_service': fields.char('ShippingService'),
        'sso_shipping_service_additional_Cost': fields.float('ShippingServiceAdditionalCost'),
        'sso_shipping_service_cost': fields.float('ShippingServiceCost'),
        'sso_shipping_service_priority': fields.integer('ShippingServicePriority'),
        'shipping_type': fields.selection([
            ('Calculated', 'Calculated'),
            ('CalculatedDomesticFlatInternational', 'CalculatedDomesticFlatInternational'),
            ('CustomCode', 'CustomCode'),
            ('Flat', 'Flat'),
            ('FlatDomesticCalculatedInternational', 'FlatDomesticCalculatedInternational'),
            ('FreightFlat', 'FreightFlat'),
            ('NotSpecified', 'NotSpecified'),
        ], 'ShippingType'),
        'ebay_item_ids': fields.one2many('ebay.item', 'shipping_details_id', 'Item'),
    }
    
    _defaults = {
        'isso_shipping_service_priority': 1,
        'sso_shipping_service_priority': 1,
        'shipping_type': 'Flat',
    }
    
ebay_shippingdetails()

class ebay_ship2locations(osv.osv):
    _name = "ebay.ship2locations"
    _description = "eBay ship to locations"
    
    _columns = {
        'name': fields.char('Name', required=True),
        'ship2locations': fields.text('ShipToLocations', required=True, help="""
            For example:
                
        """),
        'ebay_item_ids': fields.one2many('ebay.item', 'ship2locations_id', 'Item'),
    }
    
    _defaults = {
    }
    
ebay_ship2locations()

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
        'buyer_requirement_details_id': fields.many2one('ebay.buyerrequirementdetails', 'BuyerRequirementDetails', ondelete='set null'),
        'buy_it_now_price': fields.float('BuyItNowPrice'),
        'condition_description_id': fields.many2one('ebay.conditiondescription', 'ConditionDescription', ondelete='set null'),
        'condition_id': fields.integer('ConditionID'),
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
            ('Chinese', 'Chinese'),
            #('CustomCode', 'CustomCode'),
            ('FixedPriceItem', 'FixedPriceItem'),
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
        'primary_category_id': fields.many2one('ebay.category', 'Category', ondelete='set null'),
        'quantity': fields.integer('Quantity'),
        'return_policy_id': fields.many2one('ebay.returnpolicy', 'ReturnPolicy', ondelete='set null'),
        'schedule_time': fields.datetime('ScheduleTime'),
        'secondary_category_id': fields.many2one('ebay.category', '2nd Category', ondelete='set null'),
        'shipping_details_id': fields.many2one('ebay.shippingdetails', 'ShippingDetails', ondelete='set null'),
        'shipping_terms_in_description': fields.boolean('ShippingTermsInDescription'),
        'ship2locations_id': fields.many2one('ebay.ship2locations', 'ShipToLocations', ondelete='set null'),
        'site': fields.char('Site', size=16),
        'product_id': fields.many2one('product.product', 'SKU', ondelete='set null'),
        'start_price': fields.float('StartPrice', required=True),
        # Storefront
        'store_category2id': fields.integer('2nd Store Category'),
        'store_category2name': fields.char('2nd Store Category'),
        'store_category_id': fields.integer('Store Category'),
        'store_category_name': fields.char('Store Category'),
        'subtitle': fields.char('SubTitle', size=55),
        'name': fields.char('Title', size=80, required=True, select=True),
        # Variations
        'variat': fields.boolean('Variat'),
        'variation_specific_name': fields.char('VariationSpecificName', size=40),
        'variations_pictures': fields.text('VariationsPictures'),
        'variation_specifics_set': fields.text('VariationSpecificsSet'),
        'variation_ids': fields.one2many('ebay.item.variation', 'ebay_item_id', 'Variantions'),
        # Additional Info
        'description_tmpl_id': fields.many2one('ebay.item.description.template', 'Template', ondelete='set null'),
        'ebay_user_id': fields.many2one('ebay.user', 'Account', required=True, domain=[('ownership','=',True)], ondelete='set null'),
        
    }
    
    _defaults = {
        'buy_it_now_price': 19.99,
        'cross_border_trade': 'North America',
        'disable_buyer_requirements': False,
        'dispatch_time_max': 2,
        'hit_counter': 'HiddenStyle',
        'include_recommendations': True,
        'listing_type': 'FixedPriceItem',
        'quantity': 1,
        'start_price': 9.99,
    }

ebay_item()

class ebay_item_description_template(osv.osv):
    _name = "ebay.item.description.template"
    _description = "eBay item description template"
    
    _columns = {
        'name': fields.char('Name', required=True, select=True),
        'ebay_item_ids': fields.one2many('ebay.item', 'description_tmpl_id', 'Item'),
    }
    
    _defaults = {
    }
    
ebay_item_description_template()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
