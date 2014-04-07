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
import sys
import os

from openerp import tools
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

sys.path.insert(0, '%s/PbApi/' % os.path.dirname(__file__))
import pbapi

class photobucket_authorize(osv.TransientModel):
    _name = 'photobucket.authorize'
    _description = 'Photobucket Authentication'
    
    _columns = {
        'consumer_id': fields.many2one('photobucket.consumer', 'Consumer'),
        'oauth_token_key': fields.char('Oauth Token Key', readonly=True),
        'oauth_token_secret': fields.char('Oauth Token Secret', readonly=True),
        'login_url': fields.char('Login URL', size=256, readonly=True),
        'state': fields.selection([
            ('confirm', 'confirm'),
            ('login', 'login')]),
    }
    
    _defaults = {
        'state': 'confirm',
    }
    
    def get_login_url(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        this = self.browse(cr, uid, ids)[0]
        
        record_id = context and context.get('active_id', False)
        consumer = self.pool.get('photobucket.consumer').browse(cr, uid, record_id, context=context)
        
        api = pbapi.PbApi(consumer.consumer_key, consumer.consumer_secret)
        api.set_response_parser('xmldomdict')
        api.login().request().post().load_token_from_response()
        
        self.write(cr, uid, ids, {'consumer_id': record_id,
                                  'login_url': api.login_url,
                                  'oauth_token_key': api.oauth_token.key,
                                  'oauth_token_secret': api.oauth_token.secret,
                                  'state': 'login'}, context=context)
        
        return {
            'name': "Photobucket Authentication",
            'type': 'ir.actions.act_window',
            'res_model': 'photobucket.authorize',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
    
    def get_oauth_token(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        this = self.browse(cr, uid, ids)[0]
        
        consumer = this.consumer_id
        
        api = pbapi.PbApi(consumer.consumer_key, consumer.consumer_secret)
        api.set_response_parser('xmldomdict')
        api.set_oauth_token(this.oauth_token_key, this.oauth_token_secret, consumer.name)
        api.login().access().post().load_token_from_response()
        
        oauth_token = api.oauth_token
        
        consumer.write(dict(
            oauth_token_key=oauth_token.key,
            oauth_token_secret=oauth_token.secret,
        ))
        
        return {'type': 'ir.actions.act_window',
            'view_mode': 'form,tree',
            'view_type': 'form',
            'res_model': 'photobucket.consumer',
            'res_id': consumer.id}

photobucket_authorize()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: