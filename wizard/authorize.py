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

from openerp import tools
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

import ebaysdk
from ebaysdk.utils import getNodeText
from ebaysdk.exception import ConnectionError
from ebaysdk.trading import Connection as Trading

class authorize(osv.TransientModel):
    _name = 'ebay.authorize'
    _description = 'eBay Authentication'
    
    _columns = {
        'sign_in_url': fields.char('SignInUrl', size=256, readonly=True),
    }
    
    def _get_sign_in_url(self, cr, uid, context):
        return self._sign_in_url
    
    _defaults = {
        'sign_in_url': _get_sign_in_url,
    }
    
    def _get_ebay_user(self, cr, uid, context=None):
        if context is None:
            context = {}
        record_id = context and context.get('active_id', False)
        user = self.pool.get('ebay.user').browse(cr, uid, record_id, context=context)
        if not user.ownership:
            raise osv.except_osv(_('Warning!'), _('You cannot authorize no ownership account %s.' % user.user_id))
        if not user.app_id or not user.dev_id or not user.cert or not user.ru_name:
            raise osv.except_osv(_('Warning!'), _('Incomplete application keys for authorization.'))
        return user
    
    def view_init(self, cr, uid, fields_list, context=None):
        user = self._get_ebay_user(cr, uid, context)
        print 'a' * 20
        session_id = user.session_id
        if not session_id:
            try:
                api = Trading(domain=self.pool.get('ebay.ebay').get_ebay_api_domain(cr, uid, user.sale_site, user.sandbox))
                              
                api.config.set('appid', user.app_id, force=True)
                api.config.set('devid', user.dev_id, force=True)
                api.config.set('certid', user.cert, force=True)
                api.execute('GetSessionID', {'RuName': user.ru_name})
                session_id = api.response_dict().SessionID
                user.write({'session_id': session_id})
        
            except ConnectionError as e:
                raise osv.except_osv(_('Warning!'), _('Get Session ID failed: %s' % e))
            
        self._sign_in_url = self.pool.get('ebay.ebay').get_ebay_sign_in_url(cr, uid, user.sale_site, user.sandbox, user.ru_name, session_id)
        
        return False
    
    def get_token(self, cr, uid, ids, context=None):
        user = self._get_ebay_user(cr, uid, context)
        session_id = user.session_id
        if not session_id:
            raise osv.except_osv(_('Warning!'), _('User %s Session ID empty' % user.user_id))
        try:
            api = Trading(domain=self.pool.get('ebay.ebay').get_ebay_api_domain(cr, uid, user.sale_site, user.sandbox))
            api.config.set('appid', user.app_id, force=True)
            api.config.set('devid', user.dev_id, force=True)
            api.config.set('certid', user.cert, force=True)
            api.execute('FetchToken', {'SessionID': session_id})
            ebay_auth_token = api.response_dict().eBayAuthToken
            hard_expiration_time = api.response_dict().HardExpirationTime
            rest_token = api.response_dict().RESTToken
            
            user.write({'session_id': None, 'ebay_auth_token': ebay_auth_token, 'hard_expiration_time': hard_expiration_time, 'rest_token': rest_token})
        
        except ConnectionError as e:
            raise osv.except_osv(_('Warning!'), _('Get Session ID failed: %s' % e))
        
        return {'type': 'ir.actions.act_window_close'}

authorize()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: