# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import http, fields
from odoo.http import request
from datetime import date


class VariantController(http.Controller):
    @http.route(['/sale/get_combination_info'], type='json', auth="user", methods=['POST'])
    def get_combination_info(self, product_template_id, product_id, combination, add_qty, pricelist_id, **kw):
        combination = request.env['product.template.attribute.value'].browse(combination)
        pricelist = self._get_pricelist(pricelist_id)
        ProductTemplate = request.env['product.template']
        if 'context' in kw:
            ProductTemplate = ProductTemplate.with_context(**kw.get('context'))
        product_template = ProductTemplate.browse(int(product_template_id))
        res = product_template._get_combination_info(combination, int(product_id or 0), int(add_qty or 1), pricelist)
        if 'parent_combination' in kw:
            parent_combination = request.env['product.template.attribute.value'].browse(kw.get('parent_combination'))
            if not combination.exists() and product_id:
                product = request.env['product.product'].browse(int(product_id))
                if product.exists():
                    combination = product.product_template_attribute_value_ids
            res.update({
                'is_combination_possible': product_template._is_combination_possible(combination=combination, parent_combination=parent_combination),
            })
            
            product = res.get('product_id')
            producto_id = request.env['product.product'].search([('id', '=', product)])
            if pricelist and producto_id:
                today = fields.datetime.now()
                categ_ids = {}
                categ = producto_id.categ_id
                while categ:
                    categ_ids[categ.id] = True
                    categ = categ.parent_id
                categ_ids = list(categ_ids)
                results = pricelist._compute_price_rule_get_items(
                    products_qty_partner=[(producto_id, 1, False)],
                    date=today, 
                    uom_id=False, 
                    prod_tmpl_ids=[product_template.id], 
                    prod_ids=[res.get('product_id')],
                    categ_ids=categ_ids
                )
                if len(results) > 0:
                    res.update({'is_combination_possible': True})
                else:
                    res.update({'is_combination_possible': False})
            else:
                res.update({'is_combination_possible': False})
        return res

    @http.route(['/sale/create_product_variant'], type='json', auth="user", methods=['POST'])
    def create_product_variant(self, product_template_id, product_template_attribute_value_ids, **kwargs):
        return request.env['product.template'].browse(int(product_template_id)).create_product_variant(product_template_attribute_value_ids)

    def _get_pricelist(self, pricelist_id, pricelist_fallback=False):
        return request.env['product.pricelist'].browse(int(pricelist_id or 0))
