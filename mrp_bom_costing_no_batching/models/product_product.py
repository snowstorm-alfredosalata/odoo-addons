from odoo import fields, models, api, _
from odoo.tools import float_round

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_price_from_bom(self, boms_to_recompute=False):
        self.ensure_one()
        bom = self.env['mrp.bom']._bom_find(product=self)
        return self._compute_bom_price_advanced(bom, boms_to_recompute=boms_to_recompute)

    def _compute_bom_price_advanced(self, bom, boms_to_recompute=False):
        self.ensure_one()
        if not bom:
            return 0
        if not boms_to_recompute:
            boms_to_recompute = []

        work_costs = self._compute_work_costs(bom)
        other_costs = self._compute_other_costs(bom)

        material_costs = 0
        
        if not bom.subcontracted_materials:
            for line in bom.bom_line_ids:
                if line._skip_bom_line(self):
                    continue

                # Compute recursive if line has `child_line_ids`
                if line.child_bom_id and line.child_bom_id in boms_to_recompute:
                    child_total = line.product_id._compute_bom_price_advanced(line.child_bom_id, boms_to_recompute=boms_to_recompute)
                    material_costs += line.product_id.uom_id._compute_price(child_total, line.product_uom_id) * line.product_qty
                else:
                    material_costs += line.product_id.uom_id._compute_price(line.product_id.standard_price, line.product_uom_id) * line.product_qty

        return bom.product_uom_id._compute_price( (material_costs / bom.product_qty) + work_costs + other_costs, self.uom_id) 

    def _compute_work_costs(self, bom):
        return bom._compute_processing_cost_single()

    def _compute_other_costs(self, bom):
        return 0