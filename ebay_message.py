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
import urllib2
from datetime import datetime, timedelta

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
from openerp import netsvc
from openerp.tools.translate import _
import pytz
from openerp import SUPERUSER_ID

class ebay_message_synchronize(osv.TransientModel):
    _name = 'ebay.message.synchronize'
    _description = 'eBay message synchronize'
    
    _columns = {
        'number_of_days': fields.selection([
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('5', '5'),
            ('7', '7'),
            ('15', '15'),
            ('30', '30'),
            ], 'Number Of Days'),
        'message_status': fields.selection([
            ('Unanswered', 'Unanswered'),
            ('Answered', 'Answered'),
            ('CustomCode', 'CustomCode')], 'Message Status'),
        'sandbox_user_included': fields.boolean ('Sandbox User Included'),
    }
    
    _defaults = {
        'number_of_days': '2',
        'message_status': 'Unanswered',
        'sandbox_user_included': False,
    }
    
    def view_init(self, cr, uid, fields_list, context=None):
        return False
    
    def action_sync(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        this = self.browse(cr, uid, ids)[0]
        ebay_ebay_obj = self.pool.get('ebay.ebay')
        ebay_message_obj =  self.pool.get('ebay.message')
        ebay_message_media_obj =  self.pool.get('ebay.message.media')
        
        end_creation_time = datetime.now()
        start_creation_time = end_creation_time - timedelta(int(this.number_of_days))
        
        for user in ebay_ebay_obj.get_auth_user(cr, uid, this.sandbox_user_included, context=context):
            entries_per_page = 100
            page_number = 1
            has_more_items = True
            while has_more_items:
                call_data=dict()
                call_data['EndCreationTime'] = end_creation_time
                call_data['MailMessageType'] = 'All'
                if this.message_status:
                    call_data['MessageStatus'] = this.message_status
                call_data['StartCreationTime'] = start_creation_time
                call_data['Pagination'] = {
                    'EntriesPerPage': entries_per_page,
                    'PageNumber': page_number,
                }
                error_msg = 'Get the messages for the specified user %s' % user.name
                reply = ebay_ebay_obj.call(cr, uid, user, 'GetMemberMessages', call_data, error_msg, context=context).response.reply
                has_more_items = reply.HasMoreItems == 'true'
                messages = reply.MemberMessage.MemberMessageExchange
                if type(messages) != list:
                    messages = [messages]
                for message in messages:
                    # find existing message
                    domain = [('message_id', '=', message.Question.MessageID)]
                    ids = ebay_message_obj.search(cr, uid, domain, context=context)
                    if ids:
                        ebay_message = ebay_message_obj.browse(cr, uid, ids[0], context=context)
                        last_modified_date = message.LastModifiedDate
                        if ebay_message.last_modified_date != ebay_ebay_obj.to_default_format(cr, uid, last_modified_date):
                            # last modified
                            pass
                    else:
                        # create new message
                        vals = dict(
                            name=message.Question.Subject,
                            body=message.Question.Body,
                            message_type=message.Question.MessageType,
                            question_type=message.Question.QuestionType,
                            recipient_or_sender_id=message.Question.SenderID,
                            sender_email=message.Question.SenderEmail,
                            message_id=message.Question.MessageID,
                            last_modified_date=message.LastModifiedDate,
                            state=message.MessageStatus,
                            type='in',
                        )
                        if message.has_key('Item'):
                            vals['item_id'] = message.Item.ItemID
                            vals['title'] = message.Item.Title
                            vals['end_time'] = message.Item.ListingDetails.EndTime
                            vals['start_time'] = message.Item.ListingDetails.StartTime
                            vals['current_price'] = message.Item.SellingStatus.CurrentPrice.value
                        ebay_message_id = ebay_message_obj.create(cr, uid, vals, context=context)
                        
                        message_medias = []
                        if message.has_key('MessageMedia'):
                            message_medias.extend(message.MessageMedia if type(message.MessageMedia) == list else [message.MessageMedia])
                        if message.Question.has_key('MessageMedia'):
                            message_medias.extend(message.Question.MessageMedia if type(message.Question.MessageMedia) == list else [message.Question.MessageMedia])
                        if message_medias:
                            for media in message_medias:
                                vals = dict(
                                    name=media.MediaName,
                                    image=base64.encodestring(urllib2.urlopen(media.MediaURL).read()),
                                    full_url=media.MediaURL,
                                    message_id=ebay_message_id,
                                )
                                ebay_message_media_obj.create(cr, uid, vals, context=context)

                page_number = page_number + 1
        
        return {'type': 'ir.actions.act_window_close'}

class ebay_message_media(osv.osv):
    _name = "ebay.message.media"
    _description = "eBay member message"
    
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
        'name': fields.char('Name', size=100, required=True),
        # image: all image fields are base64 encoded and PIL-supported
        'image': fields.binary("Image",
            help="This field holds the image used as avatar for this contact, limited to 1024x1024px"),
        'image_medium': fields.function(_get_image, fnct_inv=_set_image,
            string="Medium-sized image", type="binary", multi="_get_image",
            store={
                'ebay.message.media': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Medium-sized image of this contact. It is automatically "\
                 "resized as a 128x128px image, with aspect ratio preserved. "\
                 "Use this field in form views or some kanban views."),
        'image_small': fields.function(_get_image, fnct_inv=_set_image,
            string="Small-sized image", type="binary", multi="_get_image",
            store={
                'ebay.message.media': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Small-sized image of this contact. It is automatically "\
                 "resized as a 64x64px image, with aspect ratio preserved. "\
                 "Use this field anywhere a small image is required."),
        'has_image': fields.function(_has_image, type="boolean"),
        'full_url': fields.char('URL', readonly=True),
        'picture_format': fields.char('PictureFormat', readonly=True),
        'use_by_date': fields.datetime('UseByDate', readonly=True),
        'message_id': fields.many2one('ebay.message', 'Message', readonly=True, ondelete='cascade'),
    }
    
ebay_message_media()
    
class ebay_message(osv.osv):
    _name = "ebay.message"
    _description = "eBay member message"

    _columns = {
        'name': fields.char('Subject', required=True),
        'body': fields.text('Body'),
        'message_type': fields.selection([
            ('All', 'All'),
            ('AskSellerQuestion', 'AskSellerQuestion'),
            ('ClassifiedsBestOffer', 'ClassifiedsBestOffer'),
            ('ClassifiedsContactSeller', 'ClassifiedsContactSeller'),
            ('ContactEbayMember', 'ContactEbayMember'),
            ('ContacteBayMemberViaAnonymousEmail', 'ContacteBayMemberViaAnonymousEmail'),
            ('ContacteBayMemberViaCommunityLink', 'ContacteBayMemberViaCommunityLink'),
            ('ContactMyBidder', 'ContactMyBidder'),
            ('ContactTransactionPartner', 'ContactTransactionPartner'),
            ('CustomCode', 'CustomCode'),
            ('ResponseToASQQuestion', 'ResponseToASQQuestion'),
            ('ResponseToContacteBayMember', 'ResponseToContacteBayMember'),
            ], 'MessageType', readonly=True),
        'question_type': fields.selection([
            ('CustomCode', 'CustomCode'),
            ('CustomizedSubject', 'CustomizedSubject'),
            ('General', 'General'),
            ('MultipleItemShipping', 'MultipleItemShipping'),
            ('None', 'None'),
            ('Payment', 'Payment'),
            ('Shipping', 'Shipping'),
        ], 'QuestionType'),
        'recipient_or_sender_id': fields.char('Recipient / Sender'),
        'sender_email': fields.char('Sender Email', size=240),
        
        'item_id': fields.char('Item ID', size=38),
        'title': fields.char('Title', readonly=True),
        'end_time': fields.datetime('End Time', readonly=True),
        'start_time': fields.datetime('Start Time', readonly=True),
        'current_price': fields.float('CurrentPrice', readonly=True),
        
        'media_ids': fields.one2many('ebay.message.media', 'message_id', 'Media'),
        'message_id': fields.char('MessageID', help='ID that uniquely identifies a message for a given user.'),
        'last_modified_date': fields.datetime('LastModifiedDate', readonly=True),
        'state': fields.selection([
            ('Draft', 'Draft'),
            ('Sent', 'Sent'),
            ('CustomCode', 'CustomCode'),
            ('Unanswered', 'Unanswered'),
            ('Answered', 'Answered'),], 'MessageStatus', readonly=True),
        
        'type': fields.selection([
            ('in', 'in'),
            ('out', 'out'),
        ], 'Type', required=True, readonly=True),
        'partner_id': fields.many2one('res.partner', 'Customer'),
        'ebay_user_id': fields.many2one('ebay.user', 'eBay User', readonly=True),
        'order_id': fields.many2one('ebay.sale.order', 'Order Reference', ondelete='cascade'),
    }
    
    _defaults = {
        'question_type': 'General',
        'state': 'Draft',
        'type': 'out',
    }
    
    _order = 'last_modified_date desc'
    
    def action_reply(self, cr, uid, ids, context=None):
        for msg in self.browse(cr, uid, ids, context=context):
            pass
    
    def action_send(self, cr, uid, ids, context=None):
        for msg in self.browse(cr, uid, ids, context=context):
            pass
    
ebay_message()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: