from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    child_bom_ids = fields.One2many('mrp.bom', related="bom_id.child_ids", string="Child Bill of Materials", help="")

    def action_confirm(self):
        res = super(MrpProduction, self).action_confirm()
        self.generate_child_orders()
        return res

    def generate_child_orders(self):
        i = 1
        for bom in self.child_bom_ids:
            child = self.env['mrp.production'].create({'name': self.name + '-' + str(i), 'product_id': bom.product_id.id or bom.product_tmpl_id.product_variant_id.id, 
                         'bom_id': bom.id, 'product_qty': self.product_qty*bom.product_qty/self.bom_id.product_qty,
                         'parent_id': self.id, 'product_uom_id': bom.product_uom_id.id})

            child._onchange_move_raw()
            child.action_confirm()
            i+=1
        
    
    child_ids = fields.One2many('mrp.production', 'parent_id', readonly=True, string="Child Production Orders", help="")
    parent_id = fields.Many2one('mrp.production', readonly=True, string="Parent Production Order", ondelete="cascade", help="")

    def compute_child_count(self):
        for i in self:
            i.child_count = len(i.child_ids)

    child_count = fields.Integer(compute=compute_child_count)
    
    def action_view_children(self):
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action['domain'] = ['|', ('id', '=', self.id), ('id', 'in', self.child_ids.ids)]

        return action

    def action_view_parent(self):
        return {
            'name': _('Produce'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.production',
            'res_id': self.parent_id.id,
            'view_id': self.env.ref('mrp.mrp_production_form_view').id,
        }


class MrpCostStructure(models.AbstractModel):
    _inherit = 'report.mrp_account_enterprise.mrp_cost_structure'
    _description = 'MRP Cost Structure Report'

    def get_lines(self, productions):
        ProductProduct = self.env['product.product']
        StockMove = self.env['stock.move']
        res = []
        for product in productions.mapped('product_id'):
            mos = productions.filtered(lambda m: m.product_id == product)
            total_cost = 0.0

            #get the cost of operations
            operations = []
            Workorders = self.env['mrp.workorder'].search([('production_id', 'in', mos.ids)])
            if Workorders:
                query_str = """SELECT w.operation_id, op.name, partner.name, sum(t.duration), wc.costs_hour
                                FROM mrp_workcenter_productivity t
                                LEFT JOIN mrp_workorder w ON (w.id = t.workorder_id)
                                LEFT JOIN mrp_workcenter wc ON (wc.id = t.workcenter_id )
                                LEFT JOIN res_users u ON (t.user_id = u.id)
                                LEFT JOIN res_partner partner ON (u.partner_id = partner.id)
                                LEFT JOIN mrp_routing_workcenter op ON (w.operation_id = op.id)
                                WHERE t.workorder_id IS NOT NULL AND t.workorder_id IN %s
                                GROUP BY w.operation_id, op.name, partner.name, t.user_id, wc.costs_hour
                                ORDER BY op.name, partner.name
                            """
                self.env.cr.execute(query_str, (tuple(Workorders.ids), ))
                for op_id, op_name, user, duration, cost_hour in self.env.cr.fetchall():
                    operations.append([user, op_id, op_name, duration / 60.0, cost_hour])

            relative_manufactoring_orders = self.env['mrp.production'].search(['&', ('id', 'not in', mos.ids),
                                                                              '|', ('id', 'in', mos.mapped('parent_id').ids),
                                                                                   ('id', 'in', mos.mapped('parent_id').mapped('child_ids').ids + mos.mapped('child_ids').ids)])  

            AbsorbableWorkorders = self.env['mrp.workorder'].search([('production_id', 'in', relative_manufactoring_orders.ids)])
            absorbable_cost = 0.0
            if AbsorbableWorkorders:
                query_str = """SELECT sum(t.duration*wc.costs_hour/60)
                                FROM mrp_workcenter_productivity t
                                LEFT JOIN mrp_workorder w ON (w.id = t.workorder_id)
                                LEFT JOIN mrp_workcenter wc ON (wc.id = t.workcenter_id )
                                WHERE t.workorder_id IS NOT NULL AND t.workorder_id IN %s
                            """
                self.env.cr.execute(query_str, (tuple(AbsorbableWorkorders.ids), ))
                for cost in self.env.cr.fetchall():
                    absorbable_cost += cost[0]

            deferrable_costs_of_operations = sum(map(lambda x: x[3] * x[4], operations))
            costs_other_weight   =  sum(relative_manufactoring_orders.mapped('bom_id.cost_weight'))
            costs_own_weight    =  sum(mos.mapped('bom_id.cost_weight'))

            costs_deferred = deferrable_costs_of_operations*costs_other_weight/(costs_other_weight + costs_own_weight)
            costs_absorbed = absorbable_cost*costs_own_weight/(costs_other_weight + costs_own_weight)

            #get the cost of raw material effectively used
            raw_material_moves = []
            query_str = """SELECT sm.product_id, sm.bom_line_id, abs(SUM(svl.quantity)), abs(SUM(svl.value))
                             FROM stock_move AS sm
                       INNER JOIN stock_valuation_layer AS svl ON svl.stock_move_id = sm.id
                            WHERE sm.raw_material_production_id in %s AND sm.state != 'cancel' AND sm.product_qty != 0 AND scrapped != 't'
                         GROUP BY sm.bom_line_id, sm.product_id"""
            self.env.cr.execute(query_str, (tuple(mos.ids), ))
            for product_id, bom_line_id, qty, cost in self.env.cr.fetchall():
                raw_material_moves.append({
                    'qty': qty,
                    'cost': cost,
                    'product_id': ProductProduct.browse(product_id),
                    'bom_line_id': bom_line_id
                })
                total_cost += cost

            #get the cost of scrapped materials
            scraps = StockMove.search([('production_id', 'in', mos.ids), ('scrapped', '=', True), ('state', '=', 'done')])
            uom = mos and mos[0].product_uom_id
            mo_qty = 0
            if not all(m.product_uom_id.id == uom.id for m in mos):
                uom = product.uom_id
                for m in mos:
                    qty = sum(m.move_finished_ids.filtered(lambda mo: mo.state == 'done' and mo.product_id == product).mapped('product_qty'))
                    if m.product_uom_id.id == uom.id:
                        mo_qty += qty
                    else:
                        mo_qty += m.product_uom_id._compute_quantity(qty, uom)
            else:
                for m in mos:
                    mo_qty += sum(m.move_finished_ids.filtered(lambda mo: mo.state == 'done' and mo.product_id == product).mapped('product_qty'))
            for m in mos:
                byproduct_moves = m.move_finished_ids.filtered(lambda mo: mo.state != 'cancel' and mo.product_id != product)
            res.append({
                'product': product,
                'mo_qty': mo_qty,
                'mo_uom': uom,
                'operations': operations,
                'currency': self.env.company.currency_id,
                'raw_material_moves': raw_material_moves,
                'total_cost': total_cost,
                'scraps': scraps,
                'mocount': len(mos),
                'byproduct_moves': byproduct_moves,
                'costs_deferred': -costs_deferred,
                'costs_absorbed': costs_absorbed
            })
        return res