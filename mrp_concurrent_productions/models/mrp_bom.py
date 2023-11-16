from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_round

class MrpBom(models.Model):
    _inherit = "mrp.bom"

    child_ids = fields.One2many('mrp.bom', 'parent_id', string="Child Bill of Materials", help="")
    parent_id = fields.Many2one('mrp.bom', string="Father Bill of Materials", help="")
    cost_weight = fields.Float("Cost weight", default=1)

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('You can not create recursive relationships between BoMs.'))
        if self.parent_id and self.child_ids:
            raise ValidationError(_('BoM relationships cannot be multi layered.'))

    @api.onchange('parent_id')
    def _unset_routing(self):
        if self.parent_id:
            self.routing_id = False

    def get_cost_quota(self):
        return self.cost_weight / sum(
            ( self | self.child_ids | self.parent_id | self.parent_id.child_ids ).mapped("cost_weight")
        ) 

   
    def _compute_processing_cost_single(self):
            if self.parent_id:
                total = super(MrpBom, self.parent_id)._compute_processing_cost_single()

            else:
                total = super(MrpBom, self)._compute_processing_cost_single()

            return total * self.get_cost_quota()


class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    def _get_bom(self, bom_id=False, product_id=False, line_qty=False, line_id=False, level=False):
        lines = super(ReportBomStructure, self)._get_bom(bom_id, product_id, line_qty, line_id, level)
        lines['deferrable_costs'] = 0
        lines['absorbable_costs'] = 0

        bom = self.env['mrp.bom'].browse(bom_id)

        if bom.child_ids:
            lines['deferrable_costs'] = - lines['operations_cost'] * ( 1 - bom.get_cost_quota() )
            lines['total'] +=  lines['deferrable_costs']


        if bom.parent_id:
            operations = self._get_operation_line(bom.parent_id.routing_id, line_qty or 0, 0, bom.parent_id)
            lines['absorbable_costs'] = sum([op['total'] for op in operations]) * bom.get_cost_quota()
            lines['total'] += lines['absorbable_costs']

        return lines

    def _get_price(self, bom, factor, product):
        price = super(ReportBomStructure, self)._get_price(bom, factor, product)

        if bom.child_ids:
            operations = self._get_operation_line(bom.routing_id, factor, 0, bom)
            price -= sum([op['total'] for op in operations]) * ( 1 - bom.get_cost_quota() )

        if bom.parent_id:
            operations = self._get_operation_line(bom.parent_id.routing_id, factor, 0, bom.parent_id)
            price += sum([op['total'] for op in operations]) * bom.get_cost_quota()

        return price