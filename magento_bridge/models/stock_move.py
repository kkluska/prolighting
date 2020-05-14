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

class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def magento_stock_update(self, odoo_product_id, warehouseId):
        ctx = dict(self._context or {})
        mappingObj = self.env['connector.product.mapping'].search(
            [('name', '=', odoo_product_id)], limit=1)
        if mappingObj:
            instanceObj = mappingObj.instance_id
            mageProductId = mappingObj.ecomm_id
            if mappingObj.instance_id.warehouse_id.id == warehouseId:
                ctx['warehouse'] = warehouseId
                productObj = self.env['product.product'].with_context(
                    ctx).browse(odoo_product_id)
                if ctx.get('mob_stock_action_val') == self.env['connector.instance'].connector_stock_action:
                    productQuantity = productObj.qty_available
                else:
                    productQuantity = productObj.virtual_available + productObj.outgoing_qty
                self.synch_quantity(
                    mageProductId, productQuantity, instanceObj)
        return True

    @api.model
    def synch_quantity(self, mageProductId, productQuantity, instanceObj):
        response = self.update_quantity(mageProductId, productQuantity, instanceObj)
        if response[0] == 1:
            return True
        else:
            self.env['connector.sync.history'].create(
                {'status': 'no', 'action_on': 'product', 'action': 'c', 'error_message': response[1]})
            return False

    @api.model
    def update_quantity(self, mageProductId, productQuantity, instanceObj):
        ctx = dict(self._context or {})
        ctx['instance_id'] = instanceObj.id
        if mageProductId:
            if not instanceObj.active:
                return [0, ' Connection needs one Active Configuration setting.']
            else:
                try:
                    if type(productQuantity) == str:
                        productQuantity = productQuantity.split('.')[0]
                    if type(productQuantity) == float:
                        productQuantity = productQuantity.as_integer_ratio()[0]
                    url, user, pwd = instanceObj.name + '/index.php/api/xmlrpc', instanceObj.user, instanceObj.pwd
                    try:
                        server = xmlrpclib.Server(url)
                        session = server.login(user, pwd)
                        try:
                            stock = 1 if productQuantity > 0 else 0
                            updateData = [
                                mageProductId, {
                                    'manage_stock': 1, 'qty': productQuantity, 'is_in_stock': stock}]
                            prodResponse = server.call(
                                session, 'product_stock.update', updateData)
                            if not prodResponse:
                                return [0, ' Error in Updating Quantity for Magneto Product Id %s,Check synchronization history.' % (mageProductId)]
                            return [1, '']
                        except Exception as e:
                            return [
                                0, ' Error in Updating Quantity for Magneto Product Id %s' %
                                mageProductId]
                    except xmlrpclib.Fault as e:
                        text = 'Error, %s Magento details are Invalid.' % e
                    except IOError as e:
                        text = 'Error, %s.' % e
                    except Exception as e:
                        text = 'Error in Magento Connection.'
                    return [1, '']
                except Exception as e:
                    return [0, ' Error in Updating Quantity for Magneto Product Id %s, Reason >>%s' % (mageProductId,str(e))]
        else:
            return [0, 'Error in Updating Stock, Magento Product Id Not Found!!!']
