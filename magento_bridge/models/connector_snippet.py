# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib

from odoo import api, models
import logging
_logger = logging.getLogger(__name__)

class ConnectorSnippet(models.TransientModel):
    _inherit = "connector.snippet"

    @api.model
    def _get_ecomm_extensions(self):
        res = super(ConnectorSnippet, self)._get_ecomm_extensions().__add__([('magento', 'Magento')])
        return res

    @api.model
    def server_call(self, session, url, method, params=None):
        if session:
            _logger.debug("API Call : %r , Payload : %r",method,params)
            server = xmlrpclib.Server(url)
            mageId = 0
            try:
                if params is None:
                    mageId = server.call(session, method)
                else:
                    mageId = server.call(session, method, params)
                _logger.debug("API Response: %r",mageId)
            except xmlrpclib.Fault as e:
                _logger.debug("API Exception: %r",e)
                return [0, '\nError during synchronization (API: %s). Reason >> %s' % (method, str(e))]
            return [1, mageId]
        return [0, "No Active connection(Without Session)"]

    @api.model
    def sync_attribute_set(self, data):
        ctx = dict(self._context or {})
        res = False
        attr_set_env = self.env['magento.attribute.set']
        set_name = data.get('name')
        set_id = data.get('set_id', 0)
        if set_name and set_id:
            instance_id = ctx.get('instance_id', False)
            set_map_obj = attr_set_env.search([
                    ('set_id', '=', set_id),
                    ('instance_id', '=', instance_id)
                ], limit=1)
            if not set_map_obj:
                set_map_obj = attr_set_env.create({
                    'name': set_name,
                    'set_id': set_id,
                    'created_by': 'Magento',
                    'instance_id': instance_id
                })
            if set_map_obj:
                update_dict = {
                    'name': set_name
                }
                attribute_ids = data.get('attribute_ids', [])
                if attribute_ids:
                    update_dict['attribute_ids'] = [
                        (6, 0, attribute_ids)]
                else:
                    update_dict['attribute_ids'] = [[5]]
                res = set_map_obj.write(update_dict)
        return res
