# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

from odoo import api, fields, models
import logging

class ProductCustomerInfo(models.Model):
    _name = 'product.customerinfo'
    _description = 'Product description for a specific customer'
    
    name = fields.Many2one('res.partner', "Partner", required=True)
    product_name = fields.Char("Description", oldname="description")
    product_code = fields.Char("Code", oldname="code")

    product_tmpl_id = fields.Many2one('product.template', "Product", required=True, ondelete="cascade")
    product_id = fields.Many2one('product.product', "Product Variant", domain=lambda x: [('product_tmpl_id', '=', x.product_tmpl_id.id)])

    notes = fields.Text("Notes")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    customer_reference = fields.Char(oldname='costumer_reference', store=False, compute="_compute_customer_reference", search="_search_customer_code")

    def _compute_customer_reference(self):
        partner = self.env.context.get('partner_id', 0)
        for i in self:
            customers = i.variant_customers_ids.filtered(lambda x: x.name.id == partner)
            i.customer_reference = customers and customers[0].product_code or ""
        

    def _search_customer_code(self, operator, value):
        cinfo = self.env['product.customerinfo'].search(['|', ('product_code', operator, value), ('product_name', operator, value)])
        return [('id', 'in', cinfo.mapped('product_tmpl_id').ids)]

    customers_ids = fields.One2many('product.customerinfo', 'product_tmpl_id', "Customer-specific Info")
    variant_customers_ids = fields.One2many('product.customerinfo', 'product_tmpl_id')

    def _search_product_partner(self, operator, value):
        positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']

        if value == False:
            cinfo = self.env['product.customerinfo'].search([])
            tmpl_ids = [x.product_tmpl_id.id for x in cinfo]
            if operator in positive_operators:
                return [('id', 'not in', tmpl_ids)]
            return [('id', 'in', tmpl_ids)]

        if operator in positive_operators:
            cinfo = self.env['product.customerinfo'].search([('name', operator, value)])
            tmpl_ids = [x.product_tmpl_id.id for x in cinfo]
            return [('id', 'in', tmpl_ids)]
        else:
            cinfo = self.env['product.customerinfo'].search([('name', 'not like', '%{}%'.format(value))])
            tmpl_ids = [x.product_tmpl_id.id for x in cinfo]
            return [('id', 'not in', tmpl_ids)]

    partner_id = fields.Many2many('res.partner', "Customer", store=False, compute=lambda x: False, search=_search_product_partner)

class ProductProduct(models.Model):
    _inherit = "product.product"

    variant_customers_ids = fields.One2many('product.customerinfo', 'product_id',  "Customer-specific Info")

    customer_reference = fields.Char(oldname='costumer_reference', store=False, compute="_compute_customer_reference", search="_search_customer_code")

    def _compute_customer_reference(self):
        partner = self.env.context.get('partner_id', 0)
        for i in self:
            customers = i.variant_customers_ids.filtered(lambda x: x.name.id == partner)
            i.customer_reference = customers and customers[0].product_code or ""
            
    def _search_customer_code(self, operator, value):
        cinfo = self.env['product.customerinfo'].search(['&', ('product_id', '!=', False), '|', ('product_code', operator, value), ('product_name', operator, value)])
        cinfo_novariant = self.env['product.customerinfo'].search(['&', ('product_id', '=', False), '|', ('product_code', operator, value), ('product_name', operator, value)])

        return ['|', ('id', 'in', cinfo.mapped('product_id').ids), ('product_tmpl_id', 'in', cinfo_novariant.mapped('product_tmpl_id').ids)]

    def _search_product_partner(self, operator, value):
        positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']

        if value == False:
            cinfo = self.env['product.customerinfo'].search([])
            tmpl_ids = [x.product_tmpl_id.id for x in cinfo]
            if operator in positive_operators:
                return [('product_tmpl_id', 'not in', tmpl_ids)]
            return [('product_tmpl_id', 'in', tmpl_ids)]

        if operator in positive_operators:
            cinfo = self.env['product.customerinfo'].search([('name', operator, value)])
            tmpl_ids = [x.product_tmpl_id.id for x in cinfo]
            return [('product_tmpl_id', 'in', tmpl_ids)]
        else:
            cinfo = self.env['product.customerinfo'].search([('name', 'not like', '%{}%'.format(value))])
            tmpl_ids = [x.product_tmpl_id.id for x in cinfo]
            return [('product_tmpl_id', 'not in', tmpl_ids)]

    partner_id = fields.Many2many('res.partner', "Customer", store=False, compute=lambda x: False, search=_search_product_partner)
    
"""    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        result = super(ProductProduct, self)._name_search(name, args, operator, limit, name_get_uid)
        if self._context.get('partner_id'):
            customers_ids = self.env['product.customerinfo']._search([
                ('name', '=', self._context.get('partner_id')),
                '|',
                ('product_code', operator, name),
                ('product_name', operator, name)], access_rights_uid=name_get_uid)
            if customers_ids:
                product_ids = self._search([('variant_customers_ids', 'in', customers_ids)], limit=limit, access_rights_uid=name_get_uid)
                if not product_ids:
                    product_ids = self._search([('product_tmpl_id.customers_ids', 'in', customers_ids)], limit=limit, access_rights_uid=name_get_uid)
                res_ids = list(map(lambda x: x[0], result))
                result += [x for x in self.browse(product_ids).name_get() if x[0] not in res_ids]

        return result


    def name_get(self):
        # TDE: this could be cleaned a bit I think

        def _name_get(d):
            name = d.get('name', '')
            code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
            if code:
                name = '[%s] %s' % (code,name)
            return (d['id'], name)

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []
        company_id = self.env.context.get('company_id')

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []

        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        # Use `load=False` to not call `name_get` for the `product_tmpl_id`
        self.sudo().read(['name', 'default_code', 'product_tmpl_id'], load=False)

        product_template_ids = self.sudo().mapped('product_tmpl_id').ids

        if partner_ids:
            supplier_info = self.env['product.supplierinfo'].sudo().search([
                ('product_tmpl_id', 'in', product_template_ids),
                ('name', 'in', partner_ids),
            ])
            # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
            # Use `load=False` to not call `name_get` for the `product_tmpl_id` and `product_id`
            supplier_info.sudo().read(['product_tmpl_id', 'product_id', 'product_name', 'product_code'], load=False)
            supplier_info_by_template = {}
            for r in supplier_info:
                supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)
        for product in self.sudo():
            variant = product.product_template_attribute_value_ids._get_combination_name()

            name = variant and "%s (%s)" % (product.name, variant) or product.name
            partnerinfo = []
            if partner_ids:
                partnerinfo = [x for x in product.seller_ids if (x.name.id in partner_ids) and (x.product_id == product)]
                if not partnerinfo:
                    partnerinfo = [x for x in product.seller_ids if (x.name.id in partner_ids) and not x.product_id]
                if not partnerinfo:
                    partnerinfo = [x for x in product.customers_ids if (x.name.id in partner_ids) and (x.product_id == product)]
                if not partnerinfo:
                    partnerinfo = [x for x in product.customers_ids if (x.name.id in partner_ids) and not x.product_id]


            if partnerinfo:
                for p in partnerinfo:
                    partner_variant = p.product_name and (
                        variant and "%s (%s)" % (p.product_name, variant) or p.product_name
                        ) or False
                    mydict = {
                              'id': product.id,
                              'name': partner_variant or name,
                              'default_code': p.product_code or product.default_code,
                              }
                    temp = _name_get(mydict)
                    if temp not in result:
                        result.append(temp)
            else:
                mydict = {
                          'id': product.id,
                          'name': name,
                          'default_code': product.default_code,
                          }
                result.append(_name_get(mydict))
        return result"""