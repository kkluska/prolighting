# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models


class MagentoWebsite(models.Model):
    _name = "magento.website"
    _description = "Magento Website"

    name = fields.Char(string='Website Name', size=64, required=True)
    website_id = fields.Integer(string='Magento Webiste Id', readonly=True)
    instance_id = fields.Many2one(
        'connector.instance', string='Magento Instance')
    ecommerce_channel = fields.Selection(
        related="instance_id.ecomm_type", 
        string="eCommerce Channel", store=True)
    code = fields.Char(string='Code', size=64, required=True)
    sort_order = fields.Char(string='Sort Order', size=64)
    default_group_id = fields.Integer(string='Default Store', readonly=True)
    is_default = fields.Boolean(string='Is Default', readonly=True)
    create_date = fields.Datetime(string='Created Date', readonly=True)

    @api.model
    def _get_website(self, website):
        websiteObj = 0
        instanceId = self._context.get('instance_id')
        websiteObjs = self.search(
            [('website_id', '=', website['website_id']), ('instance_id', '=', instanceId)])
        if websiteObjs:
            websiteObj = websiteObjs[0]
        else:
            websiteDict = {
                'name' : website['name'],
                'code' : website['code'],
                'instance_id' : instanceId,
                'website_id' : website['website_id'],
                'is_default' : website['is_default'],
                'sort_order' : website['sort_order'],
                'default_group_id' : website['default_group_id']
            }
            websiteObj = self.create(websiteDict)
        return websiteObj
