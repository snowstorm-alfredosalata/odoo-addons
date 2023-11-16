# $$LICENSE_BRIEF$$

from odoo import fields, models

class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    group_id = fields.Many2one('mrp.workcenter.group', "Workcenter Group", related='workcenter_id.group_id', store=True)
    department_id = fields.Many2one('mrp.department', "Department", related='workcenter_id.department_id', store=True)
    plant_id = fields.Many2one('mrp.plant', "Plant", related='workcenter_id.plant_id', store=True)
