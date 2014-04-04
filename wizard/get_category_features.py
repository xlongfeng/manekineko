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

import base64
import cStringIO

from openerp import tools
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

class get_category_features(osv.TransientModel):
    _name = 'ebay.category.features'
    _description = 'eBay category features'
    
    _columns = {
        'ebay_user_id': fields.many2one('ebay.user', 'Account', required=True, domain=[('ownership','=',True)]),
        'category_id': fields.char('Category ID', size=10, required=True),
        'name': fields.char('File Name', readonly=True),
        'data': fields.binary('File', readonly=True),
        'state': fields.selection([
            ('option', 'option'),   # select ebay detail option
            ('download', 'download')])        # download ebay details
    }
    
    _defaults = {
        'name': 'categoryfeatures.xml',
        'state': 'option',
    }
    
    def action_download(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        this = self.browse(cr, uid, ids)[0]
        
        call_data = dict()
        call_data['AllFeaturesForCategory'] = True
        call_data['CategoryID'] = this.category_id
        call_data['ViewAllNodes'] = True
        call_data['DetailLevel'] = 'ReturnAll'
        error_msg = 'Get the ebay details list for the specified user %s' % this.ebay_user_id.name
        resp = self.pool.get('ebay.ebay').call(cr, uid, this.ebay_user_id, 'GetCategoryFeatures', call_data, error_msg, context=context).response.content
        
        buf = cStringIO.StringIO()
        buf.write(resp)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        
        this.name = "%s-%s-%s" % (this.ebay_user_id.name, this.category_id, this.name)
        
        self.write(cr, uid, ids, {'state': 'download',
                                  'data': out,
                                  'name': this.name}, context=context)
        return {
            'name': "Get Category Features",
            'type': 'ir.actions.act_window',
            'res_model': 'ebay.category.features',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

get_category_features()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: