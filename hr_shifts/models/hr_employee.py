# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

from odoo import fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    shift_id = fields.Many2one('hr.shift', 'Shift')

    def write(self, vals):
        new_shift_id = vals.get("shift_id", False)

        if new_shift_id:
            new_shift = self.env['hr.shift'].browse(new_shift_id)
            vals['resource_calendar_id'] = new_shift.current_resource_calendar_id.id

        return super(HrEmployee, self).write(vals)
            