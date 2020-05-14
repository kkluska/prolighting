# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

# Attribute Sync Operation

from odoo import models
try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib

class ConnectorSnippet(models.TransientModel):
    _inherit = "connector.snippet"

    def magento_after_order_cancel(self, connection, increment_id, ecomm_order_id=0):
        return self.magento_order_status_sync_operation(connection, 'cancel', 'sales_order.cancel', increment_id)

    def magento_after_order_shipment(self, connection, increment_id, ecomm_order_id=0):
        return self.magento_order_status_sync_operation(connection, 'shipment', 'magerpsync.order_shippment', increment_id)

    def magento_after_order_invoice(self, connection, increment_id, ecomm_order_id=0):
        return self.magento_order_status_sync_operation(connection, 'invoice', 'magerpsync.order_invoice', increment_id)

    def magento_order_status_sync_operation(self, connection, opr, api_opr, increment_id):
        text, status, ecomm_shipment = '', 'no', ''
        if connection.get('status', ''):
            session = connection.get('session', '')
            url = connection.get('url', '')
            try:
                email = self._context.get('itemData', {}).get('send_email', False)
                server = xmlrpclib.Server(url)
                msg = "{} from Odoo".format(opr.capitalize())
                order_data = [increment_id, msg, email] if opr != 'cancel' else [increment_id]
                api_response = server.call(session, api_opr, order_data)
                if api_response:
                    text = '%s of order %s has been successfully updated on magento.' % (opr, increment_id)
                    status = 'yes'
                    if opr == "shipment":
                        ecomm_shipment = api_response
                else:
                    text = 'Magento %s Error For Order %s , Error' % (opr, increment_id)
            except xmlrpclib.Fault as e:
                text = 'Error, %s Magento details are Invalid.' % e
            except IOError as e:
                text = 'Error, %s.' % e
            except Exception as e:
                text = 'Error in Magento Connection.'
        else:
            text = 'Magento %s Error For Order %s >> Could not able to connect Magento.' % (opr, increment_id)
        return {
            'text':text,
            'status': status,
            'ecomm_shipment':ecomm_shipment
        }
