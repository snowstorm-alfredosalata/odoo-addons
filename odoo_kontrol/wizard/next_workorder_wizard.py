# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class NextWorkorderWizard(models.TransientModel):
    _name = 'next.workorder.wizard'
    _description = 'Launch Next Workorder'

    # TDE FIXME: add production_id field
    next_workorder_id = fields.Many2one('mrp.workorder', 'Workorder to Launch', required=True)
    workcenter_id = fields.Many2one('mrp.workcenter',
        'Workcenter',
        default=lambda self: self.env.context.get('workcenter_id', False), required=True)

    def launch(self):
        return self.next_workorder_id.button_start()
