from odoo import api, fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _update_subcontract_order_qty(self, quantity):
        for move in self:
            quantity_change = quantity - move.product_uom_qty
            production = move.move_orig_ids.production_id.filtered(lambda x: x.state not in ['done', 'draft', 'cancel'])
            if production:
                self.env['change.production.qty'].with_context(skip_activity=True).create({
                    'mo_id': production[0].id,
                    'product_qty': production[0].product_uom_qty + quantity_change
                }).change_prod_qty()
                