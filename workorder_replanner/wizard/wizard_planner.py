from odoo import api, fields, models
from odoo.tools import date_utils, float_compare, float_round, float_is_zero
from odoo.exceptions import AccessError, UserError
import datetime, dateutil

class WorkorderPlannerWizard(models.TransientModel):
  _name = 'workorder.planner.wizard'
  _description =  'Ripianifica Workorders'

  date_start = fields.Datetime('Data di Partenza', default=fields.Datetime.now, required=True)
  ongoing_wo = fields.Boolean('Includi Ordini in corso')
  workcenter_ids = fields.Many2many('mrp.workcenter', string="Centri di lavoro") 

  def run(self):
    records = self.env['mrp.workorder'].search([('workcenter_id', 'in', self.workcenter_ids.ids), ('state', 'not in', ('done', 'cancel'))])

    for wc in self.workcenter_ids:
      start_date = self.date_start
      workorders = records.filtered(lambda x: x.workcenter_id.id == wc.id).sorted(lambda x: (x.date_planned_start, x.product_id))
      workorders.mapped('leave_id').unlink()


      for wo in workorders:
        self.plan_workorder(wo, start_date)

  def plan_workorder(self, workorder_id, start_date):
    # Schedule all work orders (new ones and those already created)
    qty_to_produce = max(workorder_id.qty_production - workorder_id.qty_produced, 0)
    qty_to_produce = workorder_id.product_uom_id._compute_quantity(qty_to_produce, workorder_id.product_id.uom_id)

    vals = {}

    # compute theoretical duration
    time_cycle = workorder_id.operation_id.time_cycle
    cycle_number = float_round(qty_to_produce / workorder_id.workcenter_id.capacity, precision_digits=0, rounding_method='UP')
    duration_expected = workorder_id.workcenter_id.time_start + workorder_id.workcenter_id.time_stop + cycle_number * time_cycle * 100.0 / workorder_id.workcenter_id.time_efficiency

    # get first free slot
    # planning 0 hours gives the start of the next attendance
    from_date = workorder_id.workcenter_id.resource_calendar_id.plan_hours(0, start_date, compute_leaves=True, resource=workorder_id.workcenter_id.resource_id, domain=[('time_type', 'in', ['leave', 'other'])])
    to_date = workorder_id.workcenter_id.resource_calendar_id.plan_hours(duration_expected / 60.0, from_date, compute_leaves=True, resource=workorder_id.workcenter_id.resource_id, domain=[('time_type', 'in', ['leave', 'other'])])

    # Create leave on chosen workcenter calendar
    leave = self.env['resource.calendar.leaves'].create({
        'name': workorder_id.production_id.name + ' - ' + workorder_id.name,
        'calendar_id': workorder_id.workcenter_id.resource_calendar_id.id,
        'date_from': from_date,
        'date_to': to_date,
        'resource_id': workorder_id.workcenter_id.resource_id.id,
        'time_type': 'other'
    })
    vals['leave_id'] = leave.id
    workorder_id.write(vals)