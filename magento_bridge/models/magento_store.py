# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################


from odoo import api, fields, models


class MagentoStore(models.Model):
    _name = "magento.store"
    _description = "Magento Store"

    name = fields.Char(string='Store Name', size=64, required=True)
    group_id = fields.Integer(string='Magento Store Id', readonly=True)
    instance_id = fields.Many2one(
        'connector.instance', string='Magento Instance')
    ecommerce_channel = fields.Selection(
        related="instance_id.ecomm_type", 
        string="eCommerce Channel", store=True)
    root_category_id = fields.Integer(string='Root Category Id', readonly=True)
    default_store_id = fields.Integer(string='Default Store Id')
    website_id = fields.Many2one('magento.website', string='Website')
    create_date = fields.Datetime(string='Created Date', readonly=True)

    @api.model
    def _get_store_group(self, group, website):
        ctx = dict(self._context or {})
        groupObj = 0
        instanceId = ctx.get('instance_id')
        groupObjs = self.search(
            [('group_id', '=', group['group_id']), ('instance_id', '=', instanceId)])
        if groupObjs:
            groupObj = groupObjs[0]
        else:
            websiteObj = self.env['magento.website']._get_website(website)
            groupDict = {
                'name' : group.get('name'),
                'website_id' : websiteObj.id,
                'group_id' : group.get('group_id'),
                'instance_id' : instanceId,
                'root_category_id' : group.get('root_category_id'),
                'default_store_id' : group.get('default_store_id')
            }
            groupObj = self.create(groupDict)
        return groupObj
