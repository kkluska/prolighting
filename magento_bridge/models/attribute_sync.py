# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

# Attribute Sync Operation

try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib
from odoo import api, models

class ConnectorSnippet(models.TransientModel):
    _inherit = "connector.snippet"

    def create_magento_product_attribute(self, name, odoo_id, connection, ecomm_attribute_code):
        status, ecomm_id, error = connection.get('status', False), 0, ''
        if status:
            url = connection.get('url', '')
            session = connection.get('session', '')
            attrribute_data = {
                'attribute_code' : ecomm_attribute_code,
                'scope' : 'global',
                'frontend_input' : 'select',
                'is_configurable' : 1,
                'is_required' : 1,
                'frontend_label' : [{'store_id': 0, 'label': name}]
            }
            try:
                mageId = self.server_call(
                    session, url, 'magerpsync.create_attribute', [attrribute_data, odoo_id, 'Odoo'])
            except xmlrpclib.Fault as e:
                return [
                    0, '\nError in creating Attribute (Code: %s).%s' %
                    (name, str(e))]
            ecomm_id = 0
            if mageId and mageId[0] > 0:
                ecomm_id, status = mageId[1], 1
            else:
                attributeData = self.server_call(
                    session, url, 'product_attribute.info', [name])
                if attributeData[0] > 0:
                    ecomm_id = attributeData[1]['attribute_id']
                    status = 1
                else:
                    status, error = 0, 'Attribute Not found at magento.'
        return {'status': status, 'ecomm_id':ecomm_id, 'error':error}

    def create_magento_product_attribute_value(self, ecomm_id, attribute_obj, ecomm_attribute_code, instance_id, connection):
        if connection.get('status', False) and ecomm_attribute_code:
            session, url = connection.get('session', ''), connection.get('url', '')
            if session and url:
                attribute_id = attribute_obj.id
                for value_obj in attribute_obj.value_ids:
                    value_id = value_obj.id
                    if not self.env['connector.option.mapping'].search([('odoo_id', '=', value_id), ('instance_id', '=', instance_id)], limit=1):
                        attrOPtionParameter = [ecomm_attribute_code, value_obj.name.strip(), value_id, value_obj.sequence, 'Odoo']
                        self.create_magento_attribute_value(url, session, attrOPtionParameter, value_id, instance_id)
        return True

    @api.model
    def create_magento_attribute_value(self, url, session, attrOPtionParameter, value_id, instance_id):
        try:
            mageId = self.server_call(session, url, 'magerpsync.create_attribute_option', attrOPtionParameter)
            if mageId[0] > 0:
                self.create_odoo_connector_mapping('connector.option.mapping', int(mageId[1]), value_id, instance_id)
        except xmlrpclib.Fault as e:
            return ' Error in creating Option( %s )' %(str(e))
        return True
