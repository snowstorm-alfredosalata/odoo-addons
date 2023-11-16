# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class WorkorderOverproduceConfirmWizard(models.TransientModel):
    _name = 'workorder.overproduce.confirm.wizard'
    _description = 'Overproduce Confirmation'

    def confirm(self):
        workorder = self.env['mrp.workorder'].browse(self.env.context.get('workorder_id')).with_context(overproduce=True)

        return workorder.record_production()