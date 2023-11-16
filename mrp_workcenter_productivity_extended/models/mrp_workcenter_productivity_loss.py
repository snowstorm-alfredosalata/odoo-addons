# $$LICENSE_BRIEF$$

from odoo import fields, models

class MrpWorkcenterProductivityLoss(models.Model):
    _inherit = "mrp.workcenter.productivity.loss"

    loss_id = fields.Many2one(string="Reason Group", domain=([]))
    graph_color = fields.Char("Color on Graphs", related="loss_id.graph_color")