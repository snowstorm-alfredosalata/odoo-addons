from odoo import api, exceptions, fields, models

class ResCompany(models.Model):
    _inherit = "res.company"

    payroll_code = fields.Char("Company Payroll Code")