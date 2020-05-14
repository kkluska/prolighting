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
from odoo import models

class ConnectorSnippet(models.TransientModel):
    _inherit = "connector.snippet"

    def create_magento_category(self, odoo_id, parent_categ_id, name, connection):
        status, ecomm_id, error = connection.get('status', False), 0, ''
        if status and odoo_id > 0:
            categDict = {
                'name' : name,
                'is_active' : 1,
                'available_sort_by' : 1,
                'default_sort_by' : 1,
                'is_anchor' : 1,
                'include_in_menu' : 1,
            }
            categData = [parent_categ_id, categDict, odoo_id, 'Odoo']
            try:
                category_response = self.server_call(
                    connection.get('session', False), connection.get('url', False), 'magerpsync.category_mapping', categData)
            except xmlrpclib.Fault as e:
                status, error = 0, ' Error in creating Category( %s ).%s' %(name, str(e))
            if category_response and category_response[0] > 0:
                ecomm_id, status = category_response[1], 1
            else:
                status, error = 0, 'Category is failed to sync'
        return {'status': status, 'ecomm_id':ecomm_id, 'error':error}

    def update_magento_category(self, update_data, ecomm_id, connection):
        status = connection.get('status', False)
        if status and ecomm_id > 0:
            parent_id = update_data.pop('parent_id', 1)
            categDict = {
                'name' : update_data.pop('name'),
                'available_sort_by' : 1,
                'default_sort_by' : 1,
            }
            updateData, session, url = [ecomm_id, categDict], connection.get('session'), connection.get('url')
            moveData = [ecomm_id, parent_id]
            category_response = self.server_call(
                session, url, 'catalog_category.update', updateData)
            self.server_call(
                session, url, 'catalog_category.move', moveData)
            status = 1 if category_response else 0
        return {'status': status}
