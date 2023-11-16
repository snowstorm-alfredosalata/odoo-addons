
from odoo import api, models, _
from odoo.exceptions import UserError

class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'
    _description = 'Product'


    def _compute_other_costs(self, bom):
        price = super(ProductProduct, self)._compute_other_costs(bom)

        if bom.subcontractor_ids:
            valid_subcontractor_count = 0
            subcontracting_price = 0

            for sub in bom.product_tmpl_id.seller_ids:
                if sub.name in bom.subcontractor_ids:
                    valid_subcontractor_count += 1
                    subcontracting_price += self.uom_id._compute_price(sub.price, sub.product_uom)

            if valid_subcontractor_count == 0:
                return price
                
            price += subcontracting_price / valid_subcontractor_count
        
        return price