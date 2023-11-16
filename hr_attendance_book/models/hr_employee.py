# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

from odoo import fields, models, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    structure_id = fields.Many2one('hr.attendance.structure', "Attendance Structure")
    payroll_code = fields.Char("Payroll Code")
    
    def action_see_books(self):
        self.ensure_one()

        return {
            'name': _('Attendance Books'),
            'domain': [('employee_id', '=', self.id)],
            'res_model': 'hr.attendance.book',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80
        }