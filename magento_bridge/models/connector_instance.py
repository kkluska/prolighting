# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import re
try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib

from odoo import api, fields, models, _
from odoo.exceptions import UserError

XMLRPC_API = '/index.php/api/xmlrpc'

class ConnectorInstance(models.Model):
    _inherit = "connector.instance"

    store_id = fields.Many2one(
        'magento.store.view', string='Default Magento Store')
    group_id = fields.Many2one(
        related="store_id.group_id",
        string="Default Store",
        readonly=True,
        store=True)
    website_id = fields.Many2one(
        related="group_id.website_id",
        string="Default Magento Website",
        readonly=True)

    def test_magento_connection(self):
        session = 0
        connection_status = False
        status = 'Magento Connection Un-successful'
        text = 'Test connection Un-successful please check the magento login credentials !!!'
        url = self.name + XMLRPC_API
        # check_mapping = self.correct_mapping
        session_generation = self.create_magento_connection({
            'url': url,
            'user': self.user,
            'pwd':self.pwd
        })
        session = session_generation.get('session', '')
        if session:
            self.set_default_magento_website(url, session)
            text = 'Test Connection with magento is successful, now you can proceed with synchronization.'
            status = "Congratulation, It's Successfully Connected with Magento Api."
            connection_status = True
        self.status = status
        res_model = 'message.wizard'
        partial = self.env['message.wizard'].create({'text': text})
        view_id = False
        # if check_mapping:
        #     self.correct_instance_mapping()
        ctx = dict(self._context or {})
        ctx['text'] = text
        ctx['instance_id'] = self.id
        self.connection_status = connection_status
        return {'name': ("Odoo Magento Bridge"),
                'view_mode': 'form',
                'res_model': res_model,
                'view_id': view_id,
                'res_id': partial.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'context': ctx,
                'target': 'new',
                }

    def _create_magento_connection(self):
        """ create a connection between Odoo and magento 
                returns: False or list"""
        instance_id = self._context.get('instance_id', False)
        session, message, instance_obj = '', '', False
        resp = {'status':False, 'message': message}
        if instance_id:
            instance_obj = self.browse(instance_id)
        else:
            active_connections = self.search([('active', '=', True), ('ecomm_type', '=', 'magento')])
            if not active_connections:
                resp['message'] = _('Error!\nPlease create the configuration part for Magento connection!!!')
            elif len(active_connections) > 1:
                resp['message'] = _('Error!\nSorry, only one Active Configuration setting is allowed.')
            else:
                instance_obj = active_connections[0]
        if instance_obj:
            session_generation = instance_obj.create_magento_connection()
            session = session_generation.get('session', '')
            if session:
                instance_obj.session = session
                resp = {
                    'url':instance_obj.name + XMLRPC_API,
                    'session':session,
                    'instance_id':instance_obj.id,
                    'status':True,
                    'message': session_generation.get('message', '')
                }
        return resp

    def create_magento_connection(self, vals={}):
        text, session = '', ''
        if not vals:
            vals = {
                'url':self.name + XMLRPC_API,
                'user':self.user,
                'pwd':self.pwd
            }
        try:
            server = xmlrpclib.Server(vals.get('url'))
            session = server.login(vals.get('user'), vals.get('pwd'))
        except xmlrpclib.Fault as e:
            text = "Error, %s Invalid Login Credentials!!!" % (e.faultString)
        except IOError as e:
            text = str(e)
        except Exception as e:
            text = "Magento Connection Error in connecting: %s" % (e)
        return {'session':session, 'message':text}

    def set_default_magento_website(self, url, session):
        for obj in self:
            store_id = obj.store_id
            ctx = dict(self._context or {})
            ctx['instance_id'] = obj.id
            if not store_id:
                store_info = self.with_context(
                    ctx)._fetch_magento_store(url, session)
                if not store_info:
                    raise UserError(
                        _('Error!\nMagento Default Website Not Found!!!'))
                else:
                    self.write(store_info)
        return True

    def _fetch_magento_store(self, url, session):
        stores = []
        storeInfo = {}
        storeViewModel = self.env['magento.store.view']
        try:
            server = xmlrpclib.Server(url)
            stores = server.call(session, 'store.list')
        except xmlrpclib.Fault as e:
            raise UserError(
                _('Error!\nError While Fetching Magento Stores!!!, %s') % e)
        for store in stores:
            if store['website']['is_default'] == '1':
                storeObj = storeViewModel._get_store_view(store)
                storeInfo.update({
                    'website_id' : int(store['website']['website_id']),
                    'store_id' : storeObj.id,
                })
                break
        return storeInfo

    @api.model
    def fetch_connection_info(self, vals):
        """
                Called by Xmlrpc from Magento
        """
        if vals.get('magento_url'):
            active_connections = self.search([('active', '=', True)])
            is_multi_mob_installed = self.env['ir.module.module'].sudo().search(
                [('name', 'in', ['odoo_magento_multi_instance', 'mob_hybrid_multi_instance']), ("state", "=", "installed")])
            if is_multi_mob_installed:
                magento_url = re.sub(r'^https?:\/\/', '', vals.get('magento_url'))
                magento_url = re.split('index.php', magento_url)[0]
                for connection_obj in active_connections:
                    act = connection_obj.name
                    act = re.sub(r'^https?:\/\/', '', act)
                    if magento_url == act or magento_url[:-1] == act:
                        return connection_obj.read(
                            ['language', 'category', 'warehouse_id'])[0]
            else:
                for connection_obj in active_connections:
                    return connection_obj.read(
                        ['language', 'category', 'warehouse_id'])[0]
        return False