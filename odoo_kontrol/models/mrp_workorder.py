from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError

from dateutil.relativedelta import relativedelta
from datetime import datetime
import pytz

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import float_compare, float_round

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'
    _order = 'date_planned_start asc'

    tablet_excluded = fields.Boolean()
    mes_ignore = fields.Boolean()

    date_deadline = fields.Datetime(related="production_id.date_deadline")
    
    worked_from = fields.Datetime("Worked From")
    worked_to   = fields.Datetime("Worked To")

    def open_tablet_view(self):
        self.ensure_one()

        if self.tablet_excluded:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.workorder',
                'views': [[self.env.ref('mrp.mrp_production_workorder_form_view_inherit').id, 'form']],
                'res_id': self.id,
                'target': 'main',
                'context': self.env.context,
                }

        return super(MrpWorkorder, self).open_tablet_view()

    def button_mes_stop(self):
        self.mes_ignore = True

    def button_mes_start(self):
        self.mes_ignore = False

    def button_start_no_tablet(self):
        self.tablet_excluded = True
        return self.button_start()

    def button_start(self):
        self.ensure_one()

        if not self.tablet_excluded:
            return super(MrpWorkorder, self).button_start()
    
        self.qty_producing = 0

        if self.state == 'progress':
            return True

        else:
            start_date = datetime.now()
            vals = {
                'state': 'progress',
                'date_start': start_date,
                'date_planned_start': start_date,
            }
            if self.date_planned_finished < start_date:
                vals['date_planned_finished'] = start_date
                
            return self.write(vals)

    def record_production(self):
        rounding = self.production_id.product_uom_id.rounding
        if (float_compare(self.qty_produced + self.qty_producing, self.production_id.product_qty, precision_rounding=rounding) >= 0) and\
           (not self.env.context.get('overproduce', False) and (not self.next_work_order_id)):
            ctx = dict(self.env.context)
            ctx['workorder_id'] = self.id

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'workorder.overproduce.confirm.wizard',
                'target': 'new',
                'views': [(self.env.ref('odoo_kontrol.view_workorder_overproduce_confirm_wizard').id, 'form')],
                'view_mode': 'form',
                'context': ctx,
                }
        
        if self.worked_from and self.worked_to and self.state not in ('done', 'cancel'):
            timeline = self.env['mrp.workcenter.productivity']
            timeline.create(self.get_interval_data())

        res = super(MrpWorkorder, self).record_production()

        if self.tablet_excluded and self.state not in ('done', 'cancel'):
            self.qty_producing = 0

        return res

    def get_interval_data(self):
        values = {
                'workorder_id': self.id,
                'workcenter_id': self.workcenter_id.id,
                'description': _('Time Tracking: ') + self.env.user.name,
                'loss_id': self.env['mrp.workcenter.productivity.loss'].search([('loss_type','=','productive')], limit=1).ids[0],
                'date_start': self.worked_from,
                'date_end': self.worked_to,
                'user_id': self.env.user.id,  # FIXME sle: can be inconsistent with company_id
                'company_id': self.company_id.id,
                'qty_produced': self.qty_producing
            }
        
        self.worked_from = False
        self.worked_to = False

        return values


    def button_pending(self):
        self.end_previous()
        self.write({'state': 'pending'})
        return True

    def increase_producing(self, qty=1):
        self.qty_producing += qty * (self.production_id.bom_id.product_uom_id.factor / self.product_uom_id.factor)

    def _compute_working_users(self):
        """ Checks whether the current user is working, all the users currently working and the last user that worked. """
        for order in self:
            order.working_user_ids = [(4, order.id) for order in order.time_ids.filtered(lambda time: not time.date_end).sorted('date_start').mapped('user_id')]
            if order.working_user_ids:
                order.last_working_user_id = order.working_user_ids[-1]
            elif order.time_ids:
                open_time_ids = order.time_ids.filtered(lambda x: x.date_end != False)
                order.last_working_user_id = open_time_ids and open_time_ids.sorted('date_end')[-1].user_id or False
            else:
                order.last_working_user_id = False
            if order.time_ids.filtered(lambda x: (x.user_id.id == self.env.user.id) and (not x.date_end) and (x.loss_type in ('productive', 'performance'))):
                order.is_user_working = True
            else:
                order.is_user_working = False


    def button_finish(self):
        result = super(MrpWorkorder, self).button_finish()

        if self.env['mrp.workorder'].search([('workcenter_id', '=', self.workcenter_id.id), ('state', 'in', ['pending', 'ready'])]):
            view = self.env.ref('odoo_kontrol.view_launch_next_workorder_form')

            return {
                'name': "",
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'next.workorder.wizard',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'context': {'workcenter_id': self.workcenter_id.id, **self.env.context},
                'target': 'new'
            }
        return result