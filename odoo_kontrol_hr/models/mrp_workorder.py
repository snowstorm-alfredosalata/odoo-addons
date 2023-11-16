from odoo import fields, models

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'
    _order = 'date_planned_start asc'

    working_employee_id = fields.Many2one('hr.employee', "Employee")

    def get_interval_data(self):
        vals = super(MrpWorkorder, self).get_interval_data()
        vals['employee_id'] = self.working_employee_id.id

        self.working_employee_id = False

        return vals