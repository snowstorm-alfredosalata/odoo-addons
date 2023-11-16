# $$LICENSE_BRIEF$$

from odoo import models, fields, api

class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'
    
    plant_id = fields.Many2one('mrp.plant', "Plant")
    department_id = fields.Many2one('mrp.department', "Department")
    group_id = fields.Many2one('mrp.workcenter.group', "Workcenter Group")
    

    group_final = fields.Boolean(compute='_compute_group_final')

    def _compute_group_final(self):
        for workcenter in self:
            workorders = self.env['mrp.workorder'].search([('workcenter_id', '=', workcenter.id)], limit=1)
            productivity_logs = self.env['mrp.workcenter.productivity'].search([('workcenter_id', '=', workcenter.id)], limit=1)

            workcenter.group_final = (len(workorders) + len(productivity_logs) != 0)
    
    @api.onchange('plant_id')
    def _onchange_plant_id(self):
        self.department_id = False
        self.group_id = False

    @api.onchange('department_id')
    def _onchange_department_id(self):
        self.group_id = False