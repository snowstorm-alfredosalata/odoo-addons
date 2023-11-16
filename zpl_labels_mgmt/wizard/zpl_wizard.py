# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api
import re

class FakeRecordset(object):
    _name = 'fake'

    def __setitem__(self, floor_number, data):
        pass

    def __getitem__(self, index):
        return self


class ZPLWizard(models.TransientModel):
    _name = 'zpl.wizard'
    _description = 'ZPL Manual Printer'

    printer_id      = fields.Many2one('zpl.printer', string='Stampante')
    format_id       = fields.Many2one('zpl.format', string='Formato')
    combo_parameter = fields.Many2one('zpl.format.variable', string='Parametro Variabile', domain=[('format_id', '=', 'format_id')])

    labels_qty      = fields.Integer('Numero di Etichette', default=1)

    combo_lines     = fields.One2many('zpl.wizard.combo_lines', 'combo_id')
    variable_ids    = fields.One2many('zpl.wizard.variable', 'wizard_id')

    simplified      = fields.Boolean("Simplified Form")
    
    from_res_model  = fields.Char("From Model", readonly=True)
    from_res_id     = fields.Char("From ID", readonly=True)

    def launch(self):
        record = FakeRecordset()

        for x in self.variable_ids:
            setattr(record, x.key, (x.field_type == 'value') and x.value or x.ref)

        if self.combo_lines:
            for line in self.combo_lines:
                setattr(record, self.combo_parameter.key, line.value)

                self.printer_id.action_print(self.format_id.id, [record], line.labels_qty)

        else:
            self.printer_id.action_print(self.format_id.id, [record], self.labels_qty)

    def _new_batch(self, printer_id=False, format_id=False, combo_parameter=False):
        action = self.env.ref('zpl_labels_mgmt.action_zpl_wizard').read()[0]

        format_id = self.env['zpl.format'].browse(format_id)
        from_record = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
        variables = []
        combo_parameter = self.env['zpl.format.variable'].search([('format_id', '=', format_id.id), ('key', '=', combo_parameter)], limit=1)

        for var in format_id.variable_ids:
            try:
                value = getattr(from_record, var.key, False)
            except:
                value = False

            value = value or (var.field_type == 'value') and var.default_value or var.default_ref
            
            if var.field_type == 'reference':
                variables.append((0,0, {'key': var.key, 'field_type': 'reference', 'ref_model': var.ref_model.id, 'ref': value and '{},{}'.format(var.ref_model.model, value.id) or False}))
            else:
                variables.append((0,0, {'key': var.key, 'field_type': 'value', 'value': value}))

        if from_record:
            from_model = self.env['ir.model'].search([('model', '=', from_record._name)])
            variables.append((0,0, {'key': 'record', 'field_type': 'reference', 'ref_model': from_model.id, 'ref': '{},{}'.format(from_record._name, from_record.id)}))
        
        wizard = self.create({'printer_id': printer_id, 'format_id': format_id.id, 'combo_parameter': combo_parameter and combo_parameter.id, 'variable_ids': variables,
                             'from_res_model': from_record._name, 'from_res_id': from_record.id })

        action['res_id'] = wizard.id

        return action
    
    @api.onchange('format_id')
    def update_prarameter_lines(self):
        from_record = False

        if self.from_res_model:
            from_record = self.env[self.from_res_model].browse(int(self.from_res_id))
            
        variables = []

        for var in self.format_id.variable_ids:
            try:
                value = getattr(from_record, var.key, False)
            except:
                value = False

            value = value or (var.field_type == 'value') and var.default_value or var.default_ref
            
            if var.field_type == 'reference':
                variables.append((0,0, {'key': var.key, 'field_type': 'reference', 'ref_model': var.ref_model.id, 'ref': value and '{},{}'.format(var.ref_model.model, value.id) or False}))
            else:
                variables.append((0,0, {'key': var.key, 'field_type': 'value', 'value': value}))

        if from_record:
            from_model = self.env['ir.model'].search([('model', '=', from_record._name)])
            variables.append((0,0, {'key': 'record', 'field_type': 'reference', 'ref_model': from_model.id, 'ref': '{},{}'.format(from_record._name, from_record.id)}))
        
        self.write({'combo_lines': False, 'combo_parameter': False, 'variable_ids': False})
        self.write({'variable_ids': variables})
        


class ZPLVariable(models.TransientModel):
    _name = 'zpl.wizard.variable'
    _description = "ZPL Wizard Variables"
    _rec_name = "key"

    wizard_id = fields.Many2one('zpl.wizard', required=True, ondelete="cascade")

    key             = fields.Char('Campo', required=True)

    field_type      = fields.Selection([('value', 'Valore'), ('reference', 'Riferimento')], required=True, default='value', string="Tipo Campo")
    value   = fields.Char('Valore di Default')


    @api.model
    def _selection_target_model(self):
        models = self.env['ir.model'].search([])
        return [(model.model, model.name) for model in models]
        
    ref_model   = fields.Many2one('ir.model', "Tabella di Riferimento")
    ref = fields.Reference(
        string='Record di Default', selection='_selection_target_model')

class ZplWizardComboLines(models.TransientModel):
    _name = 'zpl.wizard.combo_lines'
    _description = "ZPL Wizard Combo Variable"

    value       = fields.Char('Value')
    labels_qty  = fields.Integer('Quantity')

    combo_id = fields.Many2one('zpl.wizard', required=True, ondelete="cascade")