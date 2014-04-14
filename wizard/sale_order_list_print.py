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

from datetime import datetime
import base64
import cStringIO

import xlwt

from openerp import tools
from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _

class ebay_sale_order_list_print(osv.TransientModel):
    _name = 'ebay.sale.order.list.print'
    _description = 'ebay sale order list print'
    
    _columns = {
        'count': fields.integer('Item record count', readonly=True),
        'carrier': fields.selection([
            ('carrier-4px', '4px'),
            ('carrier-sfc', 'sfc'),
        ], 'Logistics Carrier'),
        'name': fields.char('Filename', readonly=True),
        'data': fields.binary('File', readonly=True),
        'state': fields.selection([
            ('option', 'option'),
            ('download', 'download'),
        ], 'State'),
    }
    
    def _get_count(self, cr, uid, context=None):
        if context is None:
            context = {}
        record_ids = context and context.get('active_ids', False)
        return len(record_ids)
    
    _defaults = {
        'count': _get_count,
        'carrier': 'carrier-4px',
        'state': 'option'
    }
    
    def carrier_4px_format(self, cr, uid, orders, context=None):
        headers = [
            u'客户单号',
            u'服务商单号',
            u'运输方式',
            u'目的国家',
            u'寄件人公司名',
            u'寄件人姓名',
            u'寄件人地址',
            u'寄件人电话',
            u'寄件人邮编',
            u'寄件人传真',
            u'收件人公司名',
            u'收件人姓名',
            u'州 \ 省',
            u'城市',
            u'联系地址',
            u'收件人电话',
            u'收件人邮箱',
            u'收件人邮编',
            u'收件人传真',
            u'买家ID',
            u'交易ID',
            u'保险类型',
            u'保险价值',
            u'订单备注',
            u'重量',
            u'是否退件',
            u'海关报关品名1', u'配货信息1', u'申报价值1', u'申报品数量1', u'配货备注1',
            u'海关报关品名2', u'配货信息2', u'申报价值2', u'申报品数量2', u'配货备注2',
            u'海关报关品名3', u'配货信息3', u'申报价值3', u'申报品数量3', u'配货备注3',
            u'海关报关品名4', u'配货信息4', u'申报价值4', u'申报品数量4', u'配货备注4',
            u'海关报关品名5', u'配货信息5', u'申报价值5', u'申报品数量5', u'配货备注5',
        ]
        
        header_width = {
            u'收件人姓名': (1 + 32) * 256,
            u'州 \ 省': (1 + 32) * 256,
            u'城市': (1 + 32) * 256,
            u'联系地址': (1 + 64) * 256,
            u'订单备注': (1 + 64) * 256,
            u'海关报关品名1': (1 + 64) * 256, u'配货信息1': (1 + 64) * 256, u'配货备注1': (1 + 64) * 256,
            u'海关报关品名2': (1 + 64) * 256, u'配货信息2': (1 + 64) * 256, u'配货备注2': (1 + 64) * 256,
            u'海关报关品名3': (1 + 64) * 256, u'配货信息3': (1 + 64) * 256, u'配货备注3': (1 + 64) * 256,
            u'海关报关品名4': (1 + 64) * 256, u'配货信息4': (1 + 64) * 256, u'配货备注4': (1 + 64) * 256,
            u'海关报关品名5': (1 + 64) * 256, u'配货信息5': (1 + 64) * 256, u'配货备注5': (1 + 64) * 256,
        }
        
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Delivery Slip')
        
        for i, name in enumerate(headers):
            worksheet.write(0, i, name)
            width = header_width.get(name, 0)
            if width:
                worksheet.col(i).width = width
            
        for i, order in enumerate(orders):
            row = i + 1
            for key, value in order.items():
                col = headers.index(key)
                worksheet.write(row, col, value)
        
        return workbook
    
    def _prepare_order(self, cr, uid, ebay_sale_order, context=None):
        sale_order = ebay_sale_order.sale_order_ids[0]
        order_lines = sale_order.order_line
        partner = sale_order.partner_shipping_id
        shipping_service_map = {
            'hkam': 'B4',
            'hkram': 'B3',
            'sgam': 'B2',
            'sgram': 'B1',
        }
        weight = 0.0
        for line in order_lines:
            weight += line.product_id.weight * line.product_uom_qty
        order = {
            u'客户单号': sale_order.name,
            u'服务商单号': '',
            u'运输方式': shipping_service_map.get(ebay_sale_order.shipping_service, ''),
            u'目的国家': partner.country_id.code,
            #u'寄件人公司名': '',
            #u'寄件人姓名': '',
            #u'寄件人地址': '',
            #u'寄件人电话': '',
            #u'寄件人邮编': '',
            #u'寄件人传真': '',
            #u'收件人公司名': '',
            u'收件人姓名': partner.name,
            u'州 \ 省': partner.state_id.name,
            u'城市': partner.city,
            u'联系地址': '%s %s' % (partner.street, partner.street2 if partner.street2 else ''),
            u'收件人电话': partner.phone,
            u'收件人邮箱': partner.email,
            u'收件人邮编': partner.zip,
            #u'收件人传真': '',
            u'买家ID': ebay_sale_order.buyer_user_id,
            #u'交易ID': '',
            #u'保险类型': '',
            #u'保险价值': '',
            u'订单备注': sale_order.note if sale_order.note else '',
            u'重量': weight,
            #u'是否退件': '',
        }
        for i, line in enumerate(order_lines):
            order_line = {
                u'海关报关品名%s' % str(i+1): line.product_id.name,
                u'配货信息%s' % str(i+1): line.product_id.name,
                u'申报价值%s' % str(i+1): line.price_unit,
                u'申报品数量%s' % str(i+1): line.product_uom_qty,
                u'配货备注%s' % str(i+1): line.name,
            }
            order.update(order_line)
            if i+1 == 5:
                break
        return order
    
    def action_print(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        this = self.browse(cr, uid, ids)[0]
        
        record_ids = context and context.get('active_ids', False)
        orders = list()
        for ebay_sale_order in self.pool.get('ebay.sale.order').browse(cr, uid, record_ids, context=context):
            if ebay_sale_order.sale_order_ids:
                orders.append(self._prepare_order(cr, uid, ebay_sale_order, context=context))
        
        workbook = self.carrier_4px_format(cr, uid, orders, context=context)
        
        fp = cStringIO.StringIO()
        workbook.save(fp)
        out = base64.encodestring(fp.getvalue())
        fp.close()
        
        this.name = "%s-%s.xls" % (this.carrier, datetime.now().strftime('%Y%m%d-%H%M%S'))
        
        self.write(cr, uid, ids, {'state': 'download',
                                  'data': out,
                                  'name': this.name}, context=context)
        return {
            'name': "Print Delivery Slip",
            'type': 'ir.actions.act_window',
            'res_model': 'ebay.sale.order.list.print',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

ebay_sale_order_list_print()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: