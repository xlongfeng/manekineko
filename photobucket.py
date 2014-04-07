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
import base64

from openerp.osv import fields,osv
from openerp import pooler, tools
from openerp.tools.translate import _

sys.path.insert(0, '%s/PbApi/' % os.path.dirname(__file__))

import pbapi
from pbapi.error import *

class photobucket_consumer(osv.osv):
    _name = "photobucket.consumer"
    _description = "Photobucket consumer"

    _columns = {
        'name': fields.char('Consumer', required=True),
        'consumer_key': fields.char('Consumer Key', required=True),
        'consumer_secret': fields.char('Consumer Secret', required=True),
        'oauth_token_key': fields.char('Oauth Token Key', readonly=True),
        'oauth_token_secret': fields.char('Oauth Token Secret', readonly=True),
        'media_ids': fields.one2many('photobucket.media', 'consumer_id', 'Medias'),
    }
    
photobucket_consumer()
    
class photobucket_media(osv.osv):
    _name = "photobucket.media"
    _description = "Photobucket media"
    
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
        'description': fields.text('Description'),
        'browseurl': fields.char('Browse URL', readonly=True),
        'thumb': fields.char('Thumb', readonly=True),
        'url': fields.char('URL', readonly=True),
        # image: all image fields are base64 encoded and PIL-supported
        'image': fields.binary("Image", required=True,
            help="This field holds the image used as avatar for this contact, limited to 1024x1024px"),
        'image_medium': fields.function(_get_image, fnct_inv=_set_image,
            string="Medium-sized image", type="binary", multi="_get_image",
            store={
                'photobucket.media': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Medium-sized image of this contact. It is automatically "\
                 "resized as a 128x128px image, with aspect ratio preserved. "\
                 "Use this field in form views or some kanban views."),
        'image_small': fields.function(_get_image, fnct_inv=_set_image,
            string="Small-sized image", type="binary", multi="_get_image",
            store={
                'photobucket.media': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Small-sized image of this contact. It is automatically "\
                 "resized as a 64x64px image, with aspect ratio preserved. "\
                 "Use this field anywhere a small image is required."),
        'has_image': fields.function(_has_image, type="boolean"),
        'consumer_id': fields.many2one('photobucket.consumer', 'Consumer', required=True, ondelete='no action'),
    }
    
    def _get_default_consumer_id(self, cr, uid, context=None):
        res = self.pool.get('photobucket.consumer').search(cr, uid, [('oauth_token_key','!=','')], context=context)
        return res and res[0] or False
    
    _defaults = {
        'consumer_id': _get_default_consumer_id,
    }
    
    def copy(self, cr, uid, id, default=None, context=None):
        raise osv.except_osv(_('Forbbiden to duplicate'), _('Is not possible to duplicate the record, please create a new one.'))
    
    def unlink(self, cr, uid, ids, context=None):
        reserve_ids = list()
        for media in self.browse(cr, uid, ids, context=context):
            if media.url:
                consumer = media.consumer_id
                api = pbapi.PbApi(consumer.consumer_key, consumer.consumer_secret)
                api.set_response_parser('xmldomdict')
                api.set_oauth_token(consumer.oauth_token_key, consumer.oauth_token_secret, consumer.name)
                try:
                    response = api.media(media.url).delete().parsed_response
                except PbApiErrorResponse, err:
                    if err.code != '141':
                        reserve_ids.append(media.id)
                else:
                    if response['status'] != 'OK':
                        reserve_ids.append(media.id)
                        
        ids = list(set(ids) - set(reserve_ids))
        
        return super(photobucket_media, self).unlink(cr, uid, ids, context=context)
    
    def action_upload(self, cr, uid, ids, context=None):
        for media in self.browse(cr, uid, ids, context=context):
            consumer = media.consumer_id
            api = pbapi.PbApi(consumer.consumer_key, consumer.consumer_secret)
            api.set_response_parser('xmldomdict')
            api.set_oauth_token(consumer.oauth_token_key, consumer.oauth_token_secret, consumer.name)
            params = dict(
                type='base64',
                uploadfile=media.image,
                title=media.name,
                filename='oe-%s.jpg' % media.id,
            )
            if media.description:
                params['description'] = media.description
            response = api.album(consumer.name).upload(params).post().parsed_response
            if response['status'] == 'OK':
                content = response['content']
                media.write(dict(
                    browseurl=content['browseurl'],
                    thumb=content['thumb'],
                    url=content['url'],
                ))
            
photobucket_media()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
