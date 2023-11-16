# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from dateutil.relativedelta import relativedelta

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _prepare_subcontract_mo_vals(self, subcontract_move, bom):
        res = super(StockPicking, self)._prepare_subcontract_mo_vals(subcontract_move, bom)
        res['date_planned_start'] = subcontract_move.date - relativedelta(days=subcontract_move.product_id.produce_delay)
        res['date_deadline'] = res['date_planned_finished']  = subcontract_move.date
        
        return res