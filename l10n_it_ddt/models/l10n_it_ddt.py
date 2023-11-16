# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
#import logging
#from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

#from datetime import datetime, timedelta


class StockPickingGoodsDescription(models.Model):
    _name = 'l10n_it.goods_description'
    _description = "Description of Goods"

    sequence = fields.Integer('Sequence')
    name = fields.Char('Description of Goods', translatable=True, required=True, readonly=False)

class L10n_ItDDTReason(models.Model):
    _name = 'l10n_it.ddt.reason'
    _description = "Reason for Transport"
    _order = "sequence"

    sequence = fields.Integer('Sequence')
    name = fields.Char('Transport Reason', translatable=True, required=True, readonly=False)

class L10n_ItDDT(models.Model):
    _name = 'l10n_it.ddt'
    _description = "Italian-law compliant Transport Document"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name DESC"

    name = fields.Char("Transport Document Number", default="/", copy=False)
    partner_ddt_number = fields.Char("Partner DDT Number", copy=False, tracking=True)

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    date = fields.Date("Date", default=fields.Date.today(), required=True)

    def get_default_picking_type(self):
        return self.env['stock.picking.type'].search([('l10n_it_require_ddt', '=', True), ('code', '=', self.env.context.get('ddt_type', 'outgoing'))], limit=1)

    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', domain=[('l10n_it_require_ddt', '=', True)], default=get_default_picking_type, tracking=True)
    picking_type_code = fields.Selection([
        ('incoming', 'Vendors'),
        ('outgoing', 'Customers'),
        ('internal', 'Internal')], related='picking_type_id.code',
        readonly=True)

    picking_ids = fields.One2many('stock.picking', 'l10n_it_ddt_id', 'Pickings')
    return_picking_ids = fields.One2many('stock.picking', string='Return Pickings', compute="compute_return_picking_ids")

    goods_description_id = fields.Many2one('l10n_it.goods_description', 'Description of goods', default=lambda self: self.env['l10n_it.goods_description'].search([], limit=1), tracking=True)
    ddt_reason_id = fields.Many2one('l10n_it.ddt.reason', 'Reason for Transport', tracking=True)

    number_of_packages = fields.Integer("Number of Packages", default=1, tracking=True)
    shipping_weight = fields.Float("Weight in Kilograms", tracking=True)
    weight_uom_name = fields.Char(string='Weight unit of measure label', store=False, compute='_compute_weight_uom_name')

    @api.depends('shipping_weight')
    def _compute_weight_uom_name(self):
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        for ddt in self:
            ddt.weight_uom_name = weight_uom_id.name
            
    incoterm = fields.Many2one('account.incoterms', 'Incoterms',
        help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")

    carrier_type = fields.Selection([('partner', 'Partner Issued'), ('company', 'Our delivery or pickup'), ('other', 'Other Carrier')], "Carrier", default='company', readonly=False, tracking=True)
    carrier_partner_id = fields.Many2one('res.partner', "Carrier Address", tracking=True)

    partner_id = fields.Many2one('res.partner', "Addressee", required=True, tracking=True)
    partner_shipping_id = fields.Many2one('res.partner', "Shipping Address", tracking=True)
    partner_invoice_id = fields.Many2one('res.partner', "Invoice Address", tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft',
        copy=False, index=True, readonly=True, tracking=True)
    locked = fields.Boolean(tracking=True)

    def compute_return_picking_ids(self):
        pass

    move_lines = fields.One2many('stock.move', string="Stock Moves", compute="compute_move_ids")
    ux_picking_ids = fields.One2many('stock.picking', 'l10n_it_ddt_id', 'Pickings', compute="compute_move_ids", store=False)
    picking_ids_count = fields.Integer(compute="compute_move_ids")
    sales_count = fields.Integer(compute="compute_move_ids")

    @api.model
    def create(self, vals):
        if vals.get('picking_type_code', False) == 'incoming':
            vals['name'] = self.env['res.partner'].browse(vals['partner_id']).name + " - " + vals['partner_ddt_number']

        return super(L10n_ItDDT, self).create(vals)

    def write(self, vals):
        to_update = vals.keys()

        if vals.get('picking_type_code', self.picking_type_code) == 'incoming':
            if ('name' in to_update) or ('partner_id' in to_update) or ('partner_ddt_number' in to_update):
                vals['name'] = self.env['res.partner'].browse(vals.get('partner_id', self.partner_id.id)).name + " - " + vals.get('partner_ddt_number', self.partner_ddt_number)

        return super(L10n_ItDDT, self).write(vals)

    @api.depends('picking_ids')
    def compute_move_ids(self):
        for i in self:
            create_picking_id  = i.env.context.get('create_picking_id', False)
            ux_picking_ids = i.picking_ids.ids
            
            if create_picking_id:
                ux_picking_ids.append(create_picking_id)

            i.ux_picking_ids = i.env["stock.picking"].browse(set(ux_picking_ids))
            i.move_lines     = i.ux_picking_ids.mapped('move_lines').filtered(lambda x: x.state == 'done')
            i.picking_ids_count = len(i.picking_ids)
            i.sales_count = len(self.move_lines.mapped('sale_line_id.order_id'))
    
    def action_view_pickings(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        if len(self.picking_ids) > 1:
            action['domain'] = [('id', 'in', self.picking_ids.ids)]
        elif self.picking_ids:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = self.picking_ids.id
            
        action['context'] = dict(self._context, default_origin=self.name, create=False)
        return action

    def action_view_sales(self):
        self.ensure_one()
        action = self.env.ref('sale.action_quotations').read()[0]
        sales = self.move_lines.mapped('sale_line_id.order_id')

        if len(sales) > 1:
            action['domain'] = [('id', 'in', sales.ids)]
        elif sales:
            form_view = [(self.env.ref('sale.view_order_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = sales.id
            
        action['context'] = dict(self._context, default_origin=self.name, create=False)
        return action


    descriptive_lines = fields.One2many('l10n_it.ddt.descriptive.line', 'ddt_id', "Document Lines", tracking=True)

    note = fields.Text("Notes", tracking=True)

    auto_validate = fields.Boolean()

    def button_validate_picking(self):
        create_picking_id = self.env['stock.picking'].browse(self.env.context.get('create_picking_id', False))
        self.picking_ids  += create_picking_id

        if create_picking_id:
            return create_picking_id and create_picking_id.with_context({'skip_ddt_check': True}).button_validate()

    def button_validate_picking_auto_ddt(self):
        self.auto_validate = True
        return self.button_validate_picking()
        
    def button_validate(self):
        self.state = 'done'
        self.locked = True
        self.date  = fields.Date.today()
        
        if self.picking_type_code == 'outgoing':
            self.name  = self.picking_type_id.l10n_it_ddt_sequence_id.next_by_id()
        else:
            self.name = self.partner_ddt_number

    def button_lock(self):
        self.locked = not self.locked

    def unlink(self):
        if self.filtered(lambda x: x.state == 'done'):
            raise ValidationError(_("Validated DDTs cannot be deleted."))
        return super(L10n_ItDDT, self).unlink()
            
    to_invoice = fields.Boolean("Waiting for invoice", compute='_compute_to_invoice', compute_sudo=True, store=False)

    def _compute_to_invoice(self):
        to_invoice_ids = self.mapped('move_lines').filtered(lambda x: x.sale_line_id and not x.invoice_line_id).mapped('l10n_it_ddt_id').ids
        
        for ddt in self:
            ddt.to_invoice = ddt.id in to_invoice_ids

class L10n_ItDDTDescriptiveLine(models.Model):
    _name = 'l10n_it.ddt.descriptive.line'
    _description = "Italian-law compliant Transport Document Descriptive line"

    ddt_id = fields.Many2one('l10n_it.ddt', 'Transport Document', ondelete='cascade')

    name = fields.Char("Description", required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    quantity = fields.Float("Quantity", required=True)