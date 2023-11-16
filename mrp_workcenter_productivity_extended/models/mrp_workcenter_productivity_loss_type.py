# $$LICENSE_BRIEF$$

from odoo import api, fields, models

class MrpWorkcenterProductivityLossType(models.Model):
    _inherit = "mrp.workcenter.productivity.loss.type"
    _rec_name = 'name'

    @api.depends('name')
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, rec.name))
        return result
    
    name = fields.Char("Group Name")
    loss_type = fields.Selection(string="Reason Type", selection_add=[('excluded', 'Excluded from OEE Calculus'),('generic', 'Generic Loss')], ondelete={'excluded': 'set default', 'generic':'set default'})
    graph_color = fields.Char("Color on Graphs")