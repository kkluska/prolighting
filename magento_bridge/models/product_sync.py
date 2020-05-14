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

from odoo import _, api, models
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ConnectorSnippet(models.TransientModel):
    _inherit = "connector.snippet"

    def _create_product_attribute_option(self, wk_attr_line_objs):
        options_data = []
        ctx = dict(self._context or {})
        attr_val_map_model = self.env['connector.option.mapping']
        for type_obj in wk_attr_line_objs:
            get_product_option_data = {}
            mage_attr_ids = self.with_context(
                ctx)._check_attribute_sync(type_obj)
            if not mage_attr_ids :
                continue
            get_product_option_data['attribute_id'] = mage_attr_ids[0]
            get_product_option_data['label'] = type_obj.attribute_id.name
            get_product_option_data['position'] = 0
            get_product_option_data['isUseDefault'] = True
            get_product_option_data['values'] = []
            for value_id in type_obj.value_ids.ids:
                type_search = attr_val_map_model.search(
                    [('name', '=', value_id)], limit=1)
                if type_search:
                    get_product_option_data['values'].append(
                        {"value_index": type_search.ecomm_id})
            options_data.append(get_product_option_data)
        return options_data

    ############# check single attribute lines ########
    def _search_single_values(self, templ_id, attr_id):
        dic = {}
        attr_line_obj = self.env['product.template.attribute.line'].search(
            [('product_tmpl_id', '=', templ_id), ('attribute_id', '=', attr_id)], limit=1)
        if attr_line_obj and len(attr_line_obj.value_ids) == 1:
            dic[attr_line_obj.attribute_id.name] = attr_line_obj.value_ids.name
        return dic

    ############# check attributes syned return mage attribute ids ########
    def _check_attribute_sync(self, attr_line_obj):
        mage_attribute_ids = []
        ecomm_id = self.env['connector.attribute.mapping'].search(
            [('name', '=', attr_line_obj.attribute_id.id)], limit=1).ecomm_id
        if ecomm_id:
            mage_attribute_ids.append(ecomm_id)
        return mage_attribute_ids

    ############# check attributes lines and set attributes are same ########
    def _check_attribute_with_set(self, attr_set_obj, attr_line_objs):
        set_attr_objs = attr_set_obj.attribute_ids
        if not set_attr_objs:
            return {'status': 0, 'error': str(attr_set_obj.name) + ' Attribute Set Name has no attributes!!!'}
        set_attr_list = list(set_attr_objs.ids)
        for attr_line_obj in attr_line_objs:
            if attr_line_obj.attribute_id.id not in set_attr_list:
                return {'status': 0, 'error': str(attr_set_obj.name) + ' Attribute Set Name not matched with attributes!!!'}
        return {'status': 1}

    def _check_valid_attribute_set(self, attr_set_obj, templateId, instance_id):
        if instance_id and instance_id == attr_set_obj.instance_id.id:
            return attr_set_obj
        return False

    @api.model
    def get_default_attribute_set(self, instance_id):
        default_attrset = self.env['magento.attribute.set'].search(
            [('set_id', '=', 4), ('instance_id', '=', instance_id)], limit=1)
        if not default_attrset:
            raise UserError(
                _('Information!\nDefault Attribute set not Found, please sync all Attribute set from Magento!!!'))
        return default_attrset

    @api.model
    def get_magento_attribute_set(self, attribute_line_objs, instance_id):
        flag = False
        template_attribute_ids = []
        for attr in attribute_line_objs:
            template_attribute_ids.append(attr.attribute_id.id)
        attr_set_objs = self.env['magento.attribute.set'].search(
            [('instance_id', '=', instance_id)], order="set_id asc")
        for attr_set_obj in attr_set_objs:
            common_attributes = sorted(
                set(attr_set_obj.attribute_ids.ids) & set(template_attribute_ids))
            template_attribute_ids.sort()
            if common_attributes == template_attribute_ids:
                return attr_set_obj
        return False

    @api.model
    def assign_attribute_Set(self, exup_product_obj, attribute_line_objs, instance_id):
        set_obj = self.get_default_attribute_set(instance_id)
        if attribute_line_objs:
            set_obj = self.get_magento_attribute_set(
                attribute_line_objs, instance_id)
        if set_obj:
            exup_product_obj.write({'attribute_set_id': set_obj.id})
        else:
            return False
        return True

    ############# sync template variants ########
    def _sync_template_variants(self, template_obj, template_sku, instance_id, channel, url, session, connection):
        mage_variant_ids = []
        ctx = dict(self._context or {})
        for vrnt_obj in template_obj.product_variant_ids:
            exist_map_obj = vrnt_obj.connector_mapping_ids.filtered(lambda obj: obj.instance_id.id == instance_id)
            if exist_map_obj:
                mage_variant_ids.append(exist_map_obj[0].ecomm_id)
            else:
                mage_vrnt_id = self._export_specific_product(
                    vrnt_obj, template_sku, instance_id, channel, url, session, connection)
                if mage_vrnt_id and mage_vrnt_id.get('id'):
                    mage_variant_ids.append(mage_vrnt_id['id'])
        return mage_variant_ids

    def _get_product_media(self, prod_obj):
        imageDict = {
            'content' : prod_obj.image_1920,
            'mime' : 'image/jpeg'
        }
        return imageDict

    ############# fetch product details ########
    def _get_product_array(self, instance_id, channel, prod_obj, get_product_data, connection):
        prod_categs = []
        for extra_cat_obj in prod_obj.connector_categ_ids.filtered(lambda obj: obj.instance_id.id == instance_id):
            for category_obj in extra_cat_obj.categ_ids:
                mage_categ_id = self.sync_categories(category_obj, instance_id, channel, connection)
                if mage_categ_id:
                    prod_categs.append(mage_categ_id)
        status = 2
        if prod_obj.sale_ok:
            status = 1
        get_product_data.update({
            'name' : prod_obj.name,
            'short_description' : prod_obj.description_sale or ' ',
            'description' : prod_obj.description or ' ',
            'weight' : prod_obj.weight or 0.00,
            'categories' : prod_categs,
            'cost' : prod_obj.standard_price,
            'ean' : prod_obj.barcode,
            'status' : status,
        })
        if prod_obj.image_1920:
            mediaData = self._get_product_media(prod_obj)
            get_product_data.update({
                'image_data' : mediaData
            })
        return get_product_data
    
    def _get_product_qty(self, prod_obj, instance_id, stock_item_id=False, stock_id=1):
        mob_stock_action = self.env['connector.instance'].sudo().browse(instance_id).connector_stock_action
        product_qty = prod_obj.qty_available - prod_obj.outgoing_qty if mob_stock_action and mob_stock_action == "qoh" else prod_obj.virtual_available
        stock_data = {
            'manage_stock': 1,
            'qty': product_qty,
            'is_in_stock': True if product_qty else 0
        }
        return stock_data

    #############################################
    ##          single products create         ##
    #############################################

    def prodcreate(self, url, session, vrnt_obj, prodtype, sku, get_product_data, instance_id):
        odoo_id = vrnt_obj.id
        if get_product_data['currentsetname']:
            currentSet = get_product_data['currentsetname']
        else:
            currset = self.server_call(
                session, url, 'product_attribute_set.list')
            currentSet = ""
            if currset[0] > 0:
                currentSet = currset[1].get('set_id')
        try:
            prod_response = self.server_call(
                session, url, 'magerpsync.product_create', [prodtype, currentSet, sku, get_product_data, odoo_id])
        except xmlrpclib.Fault as e:
            return [0, str(odoo_id) + ':' + str(e)]
        if prod_response[0] > 0:
            ecomm_id = prod_response[1]
            self.create_odoo_connector_mapping('connector.product.mapping', ecomm_id, odoo_id, instance_id)
            return {'id':ecomm_id}
        return False

    #############################################
    ##          Specific product sync          ##
    #############################################
    def _export_specific_product(self, vrnt_obj, template_sku, instance_id, channel, url, session, connection):
        """
        @param code: product Id.
        @param context: A standard dictionary
        @return: list
        """
        get_product_data = {}
        price_extra = 0
        domain = [('product_tmpl_id', '=', vrnt_obj.product_tmpl_id.id)]
        if vrnt_obj:
            sku = vrnt_obj.default_code or 'Ref %s' % vrnt_obj.id
            prodVisibility = 1
            if template_sku == "single_variant":
                prodVisibility = 4
            crrntSetName = vrnt_obj.product_tmpl_id.attribute_set_id.set_id
            get_product_data = {
                'currentsetname' : crrntSetName,
                'visibility' : prodVisibility
            }
            if vrnt_obj.product_template_attribute_value_ids:
                for temp_value_obj in vrnt_obj.product_template_attribute_value_ids:
                    value_obj = temp_value_obj.product_attribute_value_id
                    attr_name = self.env['connector.attribute.mapping'].search(
                        [('name', '=', value_obj.attribute_id.id)], limit=1).ecomm_attribute_code or False
                    valueName = value_obj.name
                    if attr_name and valueName:
                        get_product_data[attr_name] = valueName
                    searchDomain = domain + [('product_attribute_value_id', '=', value_obj.id)]
                    attrValPriceObj = self.env['product.template.attribute.value'].search(searchDomain, limit=1)
                    if attrValPriceObj:
                        price_extra += attrValPriceObj.price_extra

            get_product_data['price'] = vrnt_obj.list_price + \
                price_extra or 0.00
            get_product_data = self._get_product_array(
                instance_id, channel, vrnt_obj, get_product_data, connection)
            stockData = self._get_product_qty(vrnt_obj, instance_id)
            get_product_data.update({'stock_data' : stockData})
            get_product_data.update({
                'websites' : [1],
                'tax_class_id' : '0'
            })
            prodtype = 'simple' if vrnt_obj.type in ['product', 'consu'] else 'virtual'
            vrnt_obj.write({'prod_type': prodtype, 'default_code': sku})
            mag_prod = self.prodcreate(url, session, vrnt_obj,
                                      prodtype, sku, get_product_data, instance_id)
            return mag_prod

    def _export_magento_specific_template(self, exup_product_obj, instance_id, channel, connection):
        status, ecomm_id, error = connection.get('status', False), 0, ''
        if status and exup_product_obj:
            url = connection.get('url', '')
            session = connection.get('session', '')
            mage_set_id = 0
            ctx = dict(self._context or {})
            get_product_data = {}
            mage_price_changes = {}
            mage_attribute_ids = []
            template_id = exup_product_obj.id
            template_sku = exup_product_obj.default_code or 'Template Ref %s' % template_id
            if not exup_product_obj.product_variant_ids:
                return {'status': 0, 'error': str(template_id) + ' No Variant Ids Found!!!'}
            else:
                wk_attr_line_objs = exup_product_obj.attribute_line_ids
                if not exup_product_obj.attribute_set_id.id:
                    res = self.assign_attribute_Set(exup_product_obj, wk_attr_line_objs, instance_id)
                    if not res:
                        return {'status': 0, 'error': str(template_id) + ' Attribute Set Name not matched with attributes!!!'}
                attr_set_obj = self.with_context(
                    ctx)._check_valid_attribute_set(exup_product_obj.attribute_set_id, template_id, instance_id)
                if not attr_set_obj:
                    return {'status': 0, 'error': str(template_id) + ' Matching attribute set not found for this instance!!!'}
                if not wk_attr_line_objs:
                    template_sku = 'single_variant'
                    mage_prod_ids = self.with_context(ctx)._sync_template_variants(
                        exup_product_obj, template_sku, instance_id, channel, url, session, connection)
                    if mage_prod_ids:
                        ecomm_id = mage_prod_ids[0]
                        self.create_odoo_connector_mapping('connector.template.mapping', ecomm_id, template_id, instance_id, is_variants=False)
                        return {'status': 1, 'ecomm_id': ecomm_id}
                    else:
                        return {'status': 0}
                else:
                    check_attribute = self.with_context(
                        ctx)._check_attribute_with_set(attr_set_obj, wk_attr_line_objs)
                    if not check_attribute.get('status', False):
                        return check_attribute
                    mage_set_id = exup_product_obj.attribute_set_id.set_id
                    if not mage_set_id:
                        return {'status': 0, 'error': str(template_id) + ' Attribute Set Name not found!!!'}
                    else:
                        for attr_line_obj in wk_attr_line_objs:
                            mageAttrIds = self.with_context(
                                ctx)._check_attribute_sync(attr_line_obj)
                            if not mageAttrIds:
                                return {'status': 0, 'error': str(template_id) + ' Attribute not syned at magento!!!'}
                            mage_attribute_ids.append(mageAttrIds[0])
                            get_product_data[
                                'configurable_attributes'] = mage_attribute_ids
                            attrName = attr_line_obj.attribute_id.name.lower(
                            ).replace(" ", "_").replace("-", "_")[:29]
                            attrMappingObj = self.env['connector.attribute.mapping'].search(
                                [('name', '=', attr_line_obj.attribute_id.id)], limit=1)
                            if attrMappingObj:
                                attrName = attrMappingObj.ecomm_attribute_code
                            valDict = self.with_context(ctx)._search_single_values(
                                template_id, attr_line_obj.attribute_id.id)
                            if valDict:
                                ctx.update(valDict)
                            domain = [('product_tmpl_id', '=', template_id)]
                            for valueObj in attr_line_obj.value_ids:
                                price_extra = 0.0
                                ##### product template and value extra price ##
                                searchDomain = domain + \
                                    [('product_attribute_value_id', '=', valueObj.id)]
                                attrPriceObjs = self.env['product.template.attribute.value'].with_context(
                                    ctx).search(searchDomain, limit=1)
                                if attrPriceObjs:
                                    price_extra = attrPriceObjs[0].price_extra
                                valueName = valueObj.name
                                if attrName in mage_price_changes:
                                    mage_price_changes[attrName].update(
                                        {valueName: price_extra})
                                else:
                                    mage_price_changes[attrName] = {
                                        valueName: price_extra}
                        mage_prod_ids = self.with_context(ctx)._sync_template_variants(
                            exup_product_obj, template_sku, instance_id, channel, url, session, connection)
                        get_product_data.update({
                            'associated_product_ids' : mage_prod_ids,
                            'price_changes' : mage_price_changes,
                            'visibility' : 4,
                            'price' : exup_product_obj.list_price or 0.00,
                            'tax_class_id' : '0'
                        })
                        get_product_data = self.with_context(ctx)._get_product_array(
                            instance_id, channel, exup_product_obj, get_product_data, connection)
                        stockData = self._get_product_qty(exup_product_obj, instance_id)
                        stockData.pop('qty', 0)
                        get_product_data.update(stock_data=stockData)
                        get_product_data['websites'] = [1]
                        templateSku = 'Template sku %s' % template_id
                        exup_product_obj.write({'prod_type': 'configurable'})
                        newProdData = [
                            'configurable',
                            mage_set_id,
                            templateSku,
                            get_product_data,
                            template_id]
                        try:
                            magProdId = self.server_call(
                                session, url, 'magerpsync.product_create', newProdData)
                        except xmlrpclib.Fault as e:
                            return {'status': 0, 'error': str(template_id) + ': ' + str(e)}
                        if magProdId[0] > 0:
                            ecomm_id = magProdId[1]
                            self.create_odoo_connector_mapping('connector.template.mapping', ecomm_id, template_id, instance_id, is_variants=True)
                            try:
                                attributeLineData = self.get_attribute_price_list(
                                    exup_product_obj.attribute_line_ids, template_id)
                                if attributeLineData:
                                    self.server_call(
                                        session, url, 'magerpsync.product_super_attribute', [
                                            magProdId[1], attributeLineData])
                            except xmlrpclib.Fault as e:
                                _logger.debug('super attribute did not updated')
                            return {'status': 1, 'ecomm_id': ecomm_id}
                        else:
                            return {'status': 0, 'error': str(template_id) + ' Error during parent sync.'}

    #############################################
    ##          update specific product        ##
    #############################################
    def _update_specific_product(self, prod_map_obj, url, session, channel, connection):
        get_product_data = {}
        prod_obj = prod_map_obj.name
        mage_prod_id = prod_map_obj.ecomm_id
        instance_obj = prod_map_obj.instance_id
        domain = [('product_tmpl_id', '=', prod_obj.product_tmpl_id.id)]
        if prod_obj and mage_prod_id:
            price_extra = 0
            if prod_obj.product_template_attribute_value_ids:
                for temp_value_obj in prod_obj.product_template_attribute_value_ids:
                    value_id = temp_value_obj.product_attribute_value_id
                    get_product_data[value_id.attribute_id.name] = value_id.name
                    searchDomain = domain + [('product_attribute_value_id', '=', value_id.id)]
                    attrPriceObjs = self.env['product.template.attribute.value'].search(searchDomain, limit=1)
                    if attrPriceObjs:
                        price_extra += attrPriceObjs.price_extra
            get_product_data['price'] = prod_obj.list_price + \
                price_extra or 0.00
            get_product_data = self._get_product_array(
                instance_obj.id, channel, prod_obj, get_product_data, connection)
            if instance_obj.inventory_sync == 'enable':
                stockData = self._get_product_qty(prod_obj, instance_obj.id)
                get_product_data.update({'stock_data' : stockData})
            updateData = [mage_prod_id, get_product_data]
            try:
                self.server_call(
                    session, url, 'magerpsync.product_update', updateData)
            except xmlrpclib.Fault as e:
                return [0, str(prod_obj.id) + str(e)]
            prod_map_obj.need_sync = 'No'
            return [1, prod_obj.id]

    def _update_magento_specific_template(self, exup_product_obj, instance_id, channel, connection):
        status = connection.get('status', False)
        if status and exup_product_obj:
            url = connection.get('url', '')
            session = connection.get('session', '')
            get_product_data = {}
            temp_obj = exup_product_obj.name
            mage_prod_ids = []
            mage_prod_id = exup_product_obj.ecomm_id
            if temp_obj and mage_prod_id:
                if temp_obj.product_variant_ids:
                    template_sku = temp_obj.default_code or 'Template Ref %s' % temp_obj.id
                    mage_prod_ids = self._sync_template_variants(temp_obj, template_sku, instance_id, channel, url, session, connection)
                    for vrnt_obj in temp_obj.product_variant_ids:
                        prod_map_obj = vrnt_obj.connector_mapping_ids.filtered(lambda obj: obj.instance_id.id == instance_id)
                        if prod_map_obj:
                            self._update_specific_product(prod_map_obj, url, session, channel, connection)
                else:
                    return {'status': 0, 'error': str(temp_obj.id) + ' No Variant Ids Found!!!'}
                if exup_product_obj.is_variants and mage_prod_ids:
                    get_product_data['price'] = temp_obj.list_price or 0.00
                    get_product_data = self._get_product_array(
                        instance_id, channel, temp_obj, get_product_data, connection)
                    get_product_data['associated_product_ids'] = mage_prod_ids
                    updateData = [mage_prod_id, get_product_data]
                    try:
                        self.server_call(
                            session, url, 'magerpsync.product_update', updateData)
                    except xmlrpclib.Fault as e:
                        return {'status': 0, 'error': str(temp_obj.id) + str(e)}
                    attributeLineData = self.get_attribute_price_list(
                        temp_obj.attribute_line_ids, temp_obj.id)
                    if attributeLineData:
                        self.server_call(
                            session, url, 'magerpsync.product_super_attribute', [
                                mage_prod_id, attributeLineData])
                exup_product_obj.need_sync = 'No'
                return {'status': 1, 'ecomm_id': temp_obj.id}

    @api.model
    def get_attribute_price_list(self, wkAttrLineObjs, templateId):
        magePriceChanges = []
        domain = [('product_tmpl_id', '=', templateId)]
        for attrLineObj in wkAttrLineObjs:
            for valueObj in attrLineObj.value_ids:
                magePriceChangesData = {}
                priceExtra = 0.0
                ##### product template and value extra price ##
                searchDomain = domain + [('product_attribute_value_id', '=', valueObj.id)]
                prodAttrPriceObjs = self.env['product.template.attribute.value'].search(searchDomain)
                if prodAttrPriceObjs:
                    priceExtra = prodAttrPriceObjs[0].price_extra
                    magePriceChangesData['price'] = priceExtra
                attrValMapObjs = self.env['connector.option.mapping'].search(
                    [('name', '=', valueObj.id)])
                if attrValMapObjs:
                    mageId = attrValMapObjs[0].ecomm_id
                    magePriceChangesData['value_id'] = mageId
                magePriceChanges.append(magePriceChangesData)
        return magePriceChanges