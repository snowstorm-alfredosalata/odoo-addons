# $$LICENSE_BRIEF$$

from odoo import models, fields

class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    production_phase = fields.Selection(
        selection=[
            ('setup', 'Set-up'),
            ('production', 'Production'),
            ('setdown', 'Set-down')
        ],
        string='Production Phase',
        default='production',
        help="Defines which phase of production this operation is describing.\nAny number of steps for each phase is allowed, but phases must progress from setup to progress and setdown linearly.\nAt least one production phase is required.\n"
             "  * Set-up: Tooling, testing and pre-production.\n"
             "  * Production: Actual production\n"
             "  * Set-down: Cleanup after production."
    )

    duration_mode = fields.Selection(
        selection=[
            ('part', 'Per part'),
            ('lot', 'Per batch'),
            ('order', 'Per order')
        ],
        string='Duration Mode',
        default='part',
        help="Defines whether standard duration refers to production of a single part, of the standard batch modulus, or to the entire order."
             "  * Per part: Final duration = Step duration * Parts to produce.\n"
             "  * Per batch: Final duration = Step duration * ( Parts to produce // Standard batch )\n"
             "  * Per order: Final duration = Step duration."
    )

    

    