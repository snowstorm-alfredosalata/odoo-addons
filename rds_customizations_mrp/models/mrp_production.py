# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'

    request_ids = fields.One2many('maintenance.request', compute='_compute_maintenances')
    maintenance_count = fields.Integer(compute='_compute_maintenances', string="Number of maintenance requests")
    on_maintenance = fields.Boolean(compute='_compute_maintenances', string="In Manutenzione", search="_search_maintenance")

    def _search_maintenance(self, operator, value):
        positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']

        open_maintenance_requests = self.env['maintenance.request'].search([('stage_id.done', '!=', True)])
        equipment_ids = open_maintenance_requests.mapped('equipment_id')

        boms_in_maintenance = self.env['mrp.bom'].search([('equipment_ids', 'in', equipment_ids.ids)])

        if (value == True) == (operator in positive_operators):
            return ['|', ('bom_id', 'in', boms_in_maintenance.ids), ('id', 'in', open_maintenance_requests.mapped('production_id').ids)]

        else:
            return ['!', '|', ('bom_id', 'in', boms_in_maintenance.ids), ('id', 'in', open_maintenance_requests.mapped('production_id').ids)]

    def _compute_maintenances(self):
        for production in self:
            equipment_ids = production.bom_id.equipment_ids # + x.workcenter_id.equipment_ids)
            production.request_ids = self.env['maintenance.request'].search(['&', ('stage_id.done', '!=', True), '|', ('equipment_id', 'in', equipment_ids.ids), ('production_id', '=', production.id)])
            production.maintenance_count = len(production.request_ids)
            production.on_maintenance = bool(production.maintenance_count)

    def open_maintenance_request_mo(self):
        self.ensure_one()
        action = {
            'name': _('Maintenance Requests'),
            'view_type': 'form',
            'view_mode': 'kanban,tree,form,pivot,graph,calendar',
            'res_model': 'maintenance.request',
            'type': 'ir.actions.act_window',
            'context': {'default_production_id': self.id,},
            'domain': [('id', 'in', self.request_ids.ids)],
        }
        if self.maintenance_count == 1:
            production = self.request_ids[0]
            action['view_mode'] = 'form'
            action['res_id'] = production.id
        return action


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    equipment_ids = fields.Many2many('maintenance.equipment', 'mrp_bom_maintenance_equipment_rel', string="Attrezzature Richieste")


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def _read_group_workcenter_id(self, workcenters, domain, order):
        return workcenters