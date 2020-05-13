# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, models

class WkSkeleton(models.TransientModel):
    _inherit = "wk.skeleton"
    _description = " Skeleton for all XML RPC imports in Odoo"

    @api.model
    def get_ecomm_href(self, getcommtype=False):
        href_list = super(WkSkeleton, self).get_ecomm_href(getcommtype)
        href_list = {}
        if getcommtype=='magento':
            href_list = {
                'user_guide':'https://webkul.com/blog/magento-openerp-bridge/',
                'rate_review':'https://store.webkul.com/Magento-OpenERP-Bridge.html#tabreviews',
                'extension':'https://store.webkul.com/Magento-Extensions/ERP.html',
                'name' : 'MAGENTO',
                'short_form' : 'Mob',
                'img_link' : '/magento_bridge/static/src/img/magento-logo.png'
            }
        return href_list

    @api.model
    def create_magento_order_lines(self, orderLineList):
        lineIds = ''
        statusMessage = ''
        if not isinstance(orderLineList, list):
            orderLineList = [orderLineList]
        for orderLineData in orderLineList:
            ecomChannel = orderLineData.pop('discount_line', False)
            orderLineData.get('product_id')
            if ecomChannel:
                orderLineData['ecommerce_channel'] = ecomChannel
                returnDict = self.create_order_shipping_and_voucher_line(
                    orderLineData)
            else:
                returnDict = self.create_sale_order_line(
                    orderLineData)
            statusMessage = returnDict.get('status_message')
            if returnDict.get('order_line_id'):
                lineIds += str(returnDict.get('order_line_id')) + ', '
        returnDict = dict(
            order_line_id=lineIds,
            status_message=statusMessage,
        )
        return returnDict