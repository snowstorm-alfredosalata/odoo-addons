
from odoo import api, models, _
from odoo.exceptions import UserError

class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'
    _description = 'Product'

    def _compute_other_costs(self, bom):
        other_costs = super(ProductProduct, self)._compute_other_costs(bom)
        
        if bom.parent_id:
            parent_costs = (bom.parent_id.product_id or bom.parent_id.product_tmpl_id.product_variant_id)._compute_work_costs(bom.parent_id)

            other_costs += parent_costs * bom.get_cost_quota()

        if bom.child_ids:
            deferreable_factor = 1 - (bom.cost_weight / (bom.cost_weight + sum(bom.child_ids.mapped('cost_weight'))))
            own_costs = self._compute_work_costs(bom)

            other_costs -= own_costs * ( 1 - bom.get_cost_quota() )

        return other_costs