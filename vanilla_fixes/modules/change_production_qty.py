from odoo import api, fields, models

class ChangeProductionQty(models.TransientModel):
    _inherit = 'change.production.qty'
    _description = 'Change Production Qty'

    @api.model
    def _update_finished_moves(self, production, _, __):
        """ Update finished product and its byproducts. This method only update
        the finished moves not done or cancel and just increase or decrease
        their quantity according the unit_ratio. It does not use the BoM, BoM
        modification during production would not be taken into consideration.
        """
        modification = {}
        for move in production.move_finished_ids:
            if move.state in ('done', 'cancel'):
                continue
            modification[move] = ( production.product_qty  + move.quantity_done - production.qty_produced, move.product_uom_qty )
            move.write({'product_uom_qty': production.product_qty + move.quantity_done - production.qty_produced})
        return modification

    def change_prod_qty(self):
        for wizard in self:
            production = wizard.mo_id
            produced = sum(production.move_finished_ids.filtered(lambda m: m.product_id == production.product_id).mapped('quantity_done'))
            production.write({'qty_produced': produced})
        
        return super(ChangeProductionQty, self).change_prod_qty()