# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import models
try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def magento_sync_tracking_no(self, picking_obj, sale_order, track_vals):
        mapObjs = self.env['connector.order.mapping'].search(
            [('odoo_order_id', '=', sale_order.id)], limit=1)
        text = "Order doesn't belongs to Magento"
        if mapObjs:
            obj= mapObjs.instance_id
            url, user, pwd = obj.name + '/index.php/api/xmlrpc', obj.user, obj.pwd
            try:
                server = xmlrpclib.Server(url)
                session = server.login(user, pwd)
                if session:
                    try:
                        server.call(session, 'sales_order_shipment.addTrack', [track_vals.get('ecom_shipment', ''), track_vals.get('carrier_code', ''), track_vals.get('title', ''), track_vals.get('track_number', '')])
                        text = 'Tracking number successfully added.'
                    except xmlrpclib.Fault as e:
                        text = "Error While Syncing Tracking Info At Magento. %s" % e
                else:
                    text = "Invalid Magento Session"
            except xmlrpclib.Fault as e:
                text = 'Error, %s Magento details are Invalid.' % e
            except IOError as e:
                text = 'Error, %s.' % e
            except Exception as e:
                text = 'Error in Magento Connection.'
        return self.env['message.wizard'].genrated_message(text)