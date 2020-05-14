# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################


from odoo import api, fields, models


class MagentoStoreView(models.Model):
    _name = "magento.store.view"
    _description = "Magento Store View"

    name = fields.Char(string='Store View Name', size=64, required=True)
    code = fields.Char(string='Code', size=64, required=True)
    view_id = fields.Integer(string='Magento Store View Id', readonly=True)
    instance_id = fields.Many2one(
        'connector.instance', string='Magento Instance')
    ecommerce_channel = fields.Selection(
        related="instance_id.ecomm_type", 
        string="eCommerce Channel", store=True)
    group_id = fields.Many2one('magento.store', string='Store Id')
    is_active = fields.Boolean(string='Active')
    sort_order = fields.Integer(string='Sort Order')
    create_date = fields.Datetime(string='Created Date', readonly=True)

    @api.depends('name', 'group_id')
    def name_get(self):
        result = []
        for record in self:
            name = record.name + \
                "\n(%s)" % (record.group_id.name) + \
                "\n(%s)" % (record.group_id.website_id.name)
            result.append((record.id, name))
        return result

    @api.model
    def _get_store_view(self, store):
        groupObj = 0
        ctx = dict(self._context or {})
        instanceId = ctx.get('instance_id')
        storeviewObjs = self.search(
            [('view_id', '=', store['store_id']), ('instance_id', '=', instanceId)])
        if storeviewObjs:
            storeviewObj = storeviewObjs[0]
        else:
            groupObj = self.env['magento.store']._get_store_group(
                store.get('group'), store.get('website'))
            viewDict = {
                'name' : store.get('name'),
                'code' : store.get('code'),
                'view_id' : store.get('store_id'),
                'group_id' : groupObj.id,
                'instance_id' : instanceId,
                'is_active' : store.get('is_active'),
                'sort_order' : store.get('sort_order')
            }
            storeviewObj = self.create(viewDict)
        return storeviewObj
