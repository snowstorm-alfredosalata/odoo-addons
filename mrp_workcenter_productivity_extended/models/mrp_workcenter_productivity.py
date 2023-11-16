# $$LICENSE_BRIEF$$

from odoo import fields, models

class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    loss_id = fields.Many2one(string="Workcenter Log Reason")
    loss_type_id = fields.Many2one('mrp.workcenter.productivity.loss.type', string='Reason Group')
    loss_type = fields.Selection(string="Reason Type", related="loss_type_id.loss_type", store=True, readonly=True)

