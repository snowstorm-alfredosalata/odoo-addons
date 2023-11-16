# $$LICENSE_BRIEF$$

from odoo import models, fields, api

class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'


    allow_setup = fields.Boolean(help="If true, allows set-up phases for this workcenter.", default=True)
    allow_setdown = fields.Boolean(help="If true, allows set-down phases for this workcenter.", default=False)

    require_setup = fields.Boolean(help="If true, only orders defining at least one set-up phase may be placed on this workcenter.", default=True)
    require_setdown = fields.Boolean(help="If true, only orders defining at least one set-down phase may be placed on this workcenter.", default=False)

    allow_production_during_setup = fields.Boolean(help="If true, the workcenter will be able to advance set-up and production operations simultaneously.")
    allow_production_during_setdown = fields.Boolean(help="If true, the workcenter will be able to advance set-down and production operations simultaneously.")

    concurrent_placements = fields.Integer(help="Number of concurrently processable manufacturing orders on this machine.\nZero signifies no limits.")

    concurrent_setups = fields.Integer(help="Number of concurrently processable set-up phases **of different manufacturing orders** on this machine.\nZero signifies no limits.")
    concurrent_productions = fields.Integer(help="Number of concurrently processable production phases **of different manufacturing orders** on this machine.\nZero signifies no limits.")
    concurrent_setdown = fields.Integer(help="Number of concurrently processable set-down phases **of different manufacturing orders** on this machine.\nZero signifies no limits.")

    _sql_constraints = [
        ('concurrent_placements_positive', 'CHECK(concurrent_placements >= 0)', 'Negative values are not allowed for concurrent placements!')
        ('concurrent_productions_positive', 'CHECK(concurrent_productions >= 0)', 'Negative values are not allowed for concurrent productions!')
        ('concurrent_setups_positive', 'CHECK(concurrent_setups >= 0)', 'Negative values are not allowed for concurrent setups!')
        ('concurrent_setdown_positive', 'CHECK(concurrent_setdown >= 0)', 'Negative values are not allowed for concurrent setdowns!')
    ]

    @api.onchange('allow_setup')
    def _onchange_allow_setup(self):
        if not self.allow_setup:
            self.require_setup = False

    @api.onchange('allow_setdown')
    def _onchange_allow_setdown(self):
        if not self.allow_setdown:
            self.require_setdown = False

    