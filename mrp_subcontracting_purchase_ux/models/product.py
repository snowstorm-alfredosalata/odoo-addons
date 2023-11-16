# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_view_outbound_pickings(self):
        """ This function returns an action that display picking related to
        manufacturing order orders. It can either be a in a list or in a form
        view, if there is only one picking to show.
        """
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings =  self.picking_ids.filtered(lambda x: x._is_subcontract()).mapped(lambda x: x._get_subcontracted_productions()).mapped('move_raw_ids').mapped('move_orig_ids.picking_id')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
            
        action['context'] = dict(self._context, default_origin=self.name, create=False)
        return action

    def action_view_production_order(self):
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action['domain'] = [('id', 'in', self.picking_ids.filtered(lambda x: x._is_subcontract()).mapped(lambda x: x._get_subcontracted_productions()).ids)]

        return action

    outbound_picking_ids = fields.Many2many(comodel_name='stock.picking',
                                    relation='purchase_order_outbound_pickings_rel',
                                    column1='purchase_id',
                                    column2='picking_id',
                                    compute='_compute_outbound_pickings', string='Spedizioni in Uscita',
                                    copy=False, store=True,)

    production_order_count = fields.Integer("Numero ordini contolavoro", compute="_compute_subcontracting_count")
    production_order_count_finished = fields.Integer("Numero ordini contolavoro evasi", compute="_compute_subcontracting_count")

    outbound_pickings_count = fields.Integer("Numero di spedizioni", compute="_compute_subcontracting_count")
    outbound_pickings_count_finished = fields.Integer("Numero di spedizioni evase", compute="_compute_subcontracting_count")
    
    inbound_pickings_count_finished = fields.Integer("Numero ricezioni evase", compute="_compute_subcontracting_count")

    outbound_pickings_state = fields.Selection(string="Stato delle Spedizioni in Uscita", selection=[('pending', 'Da Evadere'),
                                                          ('partially_done', 'Parzialmente Evaso'),
                                                          ('done', 'Evaso'), 
                                                          ('none', 'Nulla da Evadere')], compute="_compute_pickings_state", copy=False, store=True)
    inbound_pickings_state = fields.Selection(string="Stato delle Ricezioni", selection=[('pending', 'Da Evadere'),
                                                         ('partially_done', 'Parzialmente Evaso'),
                                                         ('done', 'Evaso'), 
                                                         ('none', 'Nulla da Evadere')], compute="_compute_pickings_state", copy=False, store=True)

    open_order = fields.Boolean(compute="_compute_open_order", store=True)

    @api.depends('order_line.product_uom_qty', 'order_line.qty_received', 'state')
    def _compute_open_order(self):
        for i in self:
            if i.state not in ('purchase', 'done'):
                i.open_order = False
                continue

            if i.order_line.filtered(lambda x: x.product_uom_qty > x.qty_received):
                i.open_order = True
            else:
                i.open_order = False

    @api.depends('picking_ids', 'picking_ids.state')
    def _compute_outbound_pickings(self):
        for i in self:
            pickings_with_subcontract = i.picking_ids and i.picking_ids.filtered(lambda x: x._is_subcontract())
            production_ids = pickings_with_subcontract and pickings_with_subcontract.mapped(lambda x: x._get_subcontracted_productions())
            i.outbound_picking_ids = self.env['stock.picking']

            if production_ids:
                i.outbound_picking_ids = production_ids.move_raw_ids.mapped('move_orig_ids.picking_id')

    @api.depends('picking_ids', 'picking_ids.state', 'outbound_picking_ids', 'outbound_picking_ids.state')
    def _compute_pickings_state(self):            
        for i in self:
            if (i.outbound_pickings_count > 0):
                if i.outbound_pickings_count_finished == 0:
                    i.outbound_pickings_state = "pending"
                elif i.outbound_pickings_count > i.outbound_pickings_count_finished:
                    i.outbound_pickings_state = "partially_done"
                else:
                    i.outbound_pickings_state = "done"
            else:
                i.outbound_pickings_state = "none"

            if (i.picking_count > 0):
                if i.inbound_pickings_count_finished == 0:
                    i.inbound_pickings_state = "pending"
                elif i.picking_count > i.inbound_pickings_count_finished:
                    i.inbound_pickings_state = "partially_done"
                else:
                    i.inbound_pickings_state = "done"
            else:
                i.inbound_pickings_state = "none"

    def _compute_subcontracting_count(self):
        for i in self:
            i.inbound_pickings_count_finished = len(i.picking_ids.filtered(lambda x: x.state == 'done'))

            pickings_with_subcontract = i.picking_ids and i.picking_ids.filtered(lambda x: x._is_subcontract())
            production_ids = pickings_with_subcontract and pickings_with_subcontract.mapped(lambda x: x._get_subcontracted_productions())

            if production_ids:
                i.production_order_count = len(production_ids.filtered(lambda x: x.state != 'cancel'))
                i.production_order_count_finished = len(production_ids.filtered(lambda x: x.state == 'done'))
            else:
                i.production_order_count = i.production_order_count_finished = 0

            if i.outbound_picking_ids:
                i.outbound_pickings_count = len(i.outbound_picking_ids.filtered(lambda x: x.state != 'cancel'))
                i.outbound_pickings_count_finished = len(i.outbound_picking_ids.filtered(lambda x: x.state == 'done'))
            else:
                i.outbound_pickings_count = i.outbound_pickings_count_finished = 0

    @api.depends('order_line.move_ids.returned_move_ids',
                 'order_line.move_ids.state',
                 'order_line.move_ids.picking_id')
    def _compute_picking(self):
        for order in self:
            pickings = self.env['stock.picking']
            for line in order.order_line:
                # We keep a limited scope on purpose. Ideally, we should also use move_orig_ids and
                # do some recursive search, but that could be prohibitive if not done correctly.
                moves = line.move_ids | line.move_ids.mapped('returned_move_ids')
                pickings |= moves.mapped('picking_id')
            order.picking_ids = pickings
            order.picking_count = len(pickings.filtered(lambda x: x.state != 'cancel'))



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    is_subcontractor = fields.Boolean('Subcontracted', compute='_compute_is_subcontractor', help="Choose a vendor of type subcontractor if you want to subcontract the product")

    @api.depends('order_id.partner_id', 'product_id',)
    def _compute_is_subcontractor(self):
        for supplier in self:
            boms = supplier.product_id.variant_bom_ids
            boms |= supplier.product_id.product_tmpl_id.bom_ids.filtered(lambda b: not b.product_id)
            supplier.is_subcontractor = supplier.order_id.partner_id in boms.subcontractor_ids

    ### QUICK FIX

    def _create_or_update_picking(self):
        for line in self:
            if line.product_id and line.product_id.type in ('product', 'consu'):
                # Prevent decreasing below received quantity
                if float_compare(line.product_qty, line.qty_received, line.product_uom.rounding) < 0:
                    raise UserError(_('You cannot decrease the ordered quantity below the received quantity.\n'
                                      'Create a return first.'))

                if float_compare(line.product_qty, line.qty_invoiced, line.product_uom.rounding) == -1:
                    # If the quantity is now below the invoiced quantity, create an activity on the vendor bill
                    # inviting the user to create a refund.
                    activity = self.env['mail.activity'].sudo().create({
                        'activity_type_id': self.env.ref('mail.mail_activity_data_warning').id,
                        'note': _('The quantities on your purchase order indicate less than billed. You should ask for a refund. '),
                        'res_id': line.invoice_lines[0].move_id.id,
                        'res_model_id': self.env.ref('account.model_account_move').id,
                    })
                    activity._onchange_activity_type_id()

                # If the user increased quantity of existing line or created a new line
                pickings = line.order_id.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel') and x.location_dest_id.usage in ('internal', 'transit'))
                picking = pickings and pickings[0] or False
                if not picking:
                    res = line.order_id._prepare_picking()
                    picking = self.env['stock.picking'].create(res)
                move_vals = line._prepare_stock_moves(picking)
                for move_val in move_vals:
                    self.env['stock.move']\
                        .create(move_val)\
                        ._action_confirm()\
                        ._action_assign()




class MrpAbstractWorkorder(models.AbstractModel):
    _inherit = "mrp.abstract.workorder"

    @api.model
    def _prepare_component_quantity(self, move, qty_producing, round=False):
        """ helper that computes quantity to consume (or to create in case of byproduct)
        depending on the quantity producing and the move's unit factor"""
        if move.product_id.tracking == 'serial':
            uom = move.product_id.uom_id
        else:
            uom = move.product_uom
        return move.product_uom._compute_quantity(
            qty_producing * move.unit_factor,
            uom,
            round=round
        )

class MrpProductProduce(models.TransientModel):
    _inherit = 'mrp.product.produce'

    def _generate_produce_lines(self):
        """ When the wizard is called in backend, the onchange that create the
        produce lines is not trigger. This method generate them and is used with
        _record_production to appropriately set the lot_produced_id and
        appropriately create raw stock move lines.
        """
        self.ensure_one()
        moves = (self.move_raw_ids | self.move_finished_ids).filtered(
            lambda move: move.state not in ('done', 'cancel')
        )
        for move in moves:
            qty_to_consume = self._prepare_component_quantity(move, self.qty_producing, True)
            line_values = self._generate_lines_values(move, qty_to_consume)
            self.env['mrp.product.produce.line'].create(line_values)
            
class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'

    def write(self, vals):
        if vals.get('product_qty', 1) == 0:
            vals.pop('product_qty', None)
            super(MrpProduction, self).write(vals)
            self.action_cancel()

        else:
            return super(MrpProduction, self).write(vals)


class Message(models.Model):
    """ Messages model: system notification (replacing res.log notifications),
        comments (OpenChatter discussion) and incoming emails. """
    _inherit = 'mail.message'

    def _invalidate_documents(self, model=None, res_id=None):
        """ Invalidate the cache of the documents followed by ``self``. """
        for record in self:
            model = model or record.model
            res_id = res_id or record.res_id

            if not model or not res_id:
                continue

            if issubclass(self.pool[model], self.pool['mail.thread']):
                self.env[model].invalidate_cache(fnames=[
                    'message_ids',
                    'message_unread',
                    'message_unread_counter',
                    'message_needaction',
                    'message_needaction_counter',
                ], ids=[res_id])

class StockMove(models.Model):
    _inherit = "stock.move"

    def _recompute_state(self):
        subcontracted_moves = self.filtered(lambda x: x.is_subcontract == True)
        other_moves = self.filtered(lambda x: x.is_subcontract == False)
        
        chain_recompute = self.env['stock.move']
        for move in self:
            chain_recompute |= move.move_dest_ids.filtered(lambda x: x.is_subcontract == True)

        super(StockMove, other_moves)._recompute_state()

        for move in subcontracted_moves:
            if move.state in ('cancel', 'done', 'draft'):
                continue

            raw_moves = move.move_orig_ids.production_id.move_raw_ids

            if all(orig.state in ('cancel', 'done') for orig in raw_moves):
                move.state = 'confirmed'
                continue

            if all(orig.state in ('assigned', 'cancel', 'done') for orig in raw_moves):
                move.state = 'assigned'
            elif all(orig.state in ('partially_available', 'assigned', 'cancel', 'done') for orig in raw_moves):
                move.state = 'partially_available'
            elif any(orig.state == 'waiting' for orig in raw_moves):
                move.state = 'waiting'
            else:
                move.state = 'confirmed'

        if chain_recompute:
            chain_recompute._recompute_state()


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    # -------------------------------------------------------------------------
    # Action methods
    # -------------------------------------------------------------------------

    def action_done(self):
        moves_to_fix = self.env['stock.move']
        productions = self.env['mrp.production']
        for picking in self:
            for move in picking.move_lines:
                if not move.is_subcontract:
                    continue
                productions |= move.move_orig_ids.production_id
            for subcontracted_production in productions:
                moves_to_fix |= (subcontracted_production.move_raw_ids | subcontracted_production.move_finished_ids)

        dates = dict()
        for move in moves_to_fix:
            if move.state == 'done':
                dates[move.id] = move.date

        res = super(StockPicking, self).action_done()

        for move in moves_to_fix:
            if move.id in dates.keys():
                move.date = dates[move.id]

        return res