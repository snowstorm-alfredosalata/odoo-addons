# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

from odoo import models, fields, _, api

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    l10n_it_ddt_sequence_id = fields.Many2one('ir.sequence', 'Transport Document Sequence', help="Sequence with which to numerate DDTs.")
    l10n_it_require_ddt = fields.Boolean("Group pickings into Transport Documents", help="If ticked, pickings with this picking type will be automatically assigned to Transport Documents.")
    l10n_it_transport_reason = fields.Many2many('l10n_it.ddt.reason', string="Applicable Transport Reasons")

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    l10n_it_ddt_id = fields.Many2one('l10n_it.ddt', 'Transport Document', readonly=True, copy=False)

    def button_validate(self):
        self.ensure_one()

        if not self.env.context.get('skip_ddt') \
           and not self.l10n_it_ddt_id \
           and self.picking_type_id.l10n_it_require_ddt:

            view = self.env.ref('l10n_it_ddt.l10n_it_ddt_wizard')
            defaults = self.get_ddt_defaults()

            ddt = self.env['l10n_it.ddt'].search([('state', '=', 'draft'), 
                                                  ('partner_id', '=', defaults.get('default_partner_id')), ('partner_invoice_id', '=', defaults.get('default_partner_invoice_id')), 
                                                  ('picking_type_id', '=', defaults.get('default_picking_type_id'))])

            return {
                    'name': _('New Transport Document'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'l10n_it.ddt',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': ddt and ddt.id or False,
                    'context': {'create_picking_id': self.id, **defaults, **self.env.context},
                }
                
        return super(StockPicking, self).button_validate()
    

    def action_done(self):
        res = super(StockPicking, self).action_done()

        if self.l10n_it_ddt_id and self.l10n_it_ddt_id.auto_validate:
            self.l10n_it_ddt_id.button_validate()

        self._compute_state()  
        return res


    def get_ddt_defaults(self):
        partner_id = self.partner_id
        partner_invoice_id = self.partner_id

        if (self.picking_type_code == "outgoing") and self.sale_id:
            partner_id = self.sale_id.partner_id
            partner_invoice_id = self.sale_id.partner_invoice_id or partner_id
        
        ddt_reason         = self.picking_type_id.l10n_it_transport_reason[:1]

        return {'default_picking_ids': [(4,self.id)], 'default_picking_type_id': self.picking_type_id.id, 
                'default_partner_id': partner_id.id, 'default_partner_shipping_id': self.partner_id.id, 
                'default_partner_invoice_id': partner_invoice_id and partner_invoice_id.id ,
                'default_ddt_reason_id': ddt_reason and ddt_reason.id}

    def get_ddt_default_values(self):
        return {'picking_ids': [(4,self.id)], 'picking_type_id': self.picking_type_id.id, 'partner_id': self.partner_id.id}


