# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

'''
#
#   This whole section was added to ease contract info lookup for non-hr management personell.
#   At RDS we want production officers to know contract type and/or expiry of their personell,
#   but we don't want to grant access to the actual contracts.
#   
#   We also add an icon to Employee Tags which is used in employee badge for flavouring.
#
'''

from odoo import api, fields, models
from odoo.addons.resource.models.resource import HOURS_PER_DAY

class Employee(models.Model):
    _name = 'hr.employee'
    _inherit = ['hr.employee']

    def _compute_contract_info(self):
        for i in self:
            # Computed as sudo because not all users have access to hr.contract.
            all_emp_contracts = i.sudo().env['hr.contract'].search(['&', ('state','in', ['open', 'pending','close']), ('employee_id', '=', i.ids[0])]).sorted(key=lambda r: r.date_start)
            running_contracts = all_emp_contracts.filtered(lambda s: s.state in ['open', 'pending']).sorted(key=lambda r: r.date_start)
            i.fixed_term = True
            i.first_employed = False
            i.current_contract_start = False
            i.current_contract_end = False
            i.last_employed = False

            if all_emp_contracts:
                i.first_employed = all_emp_contracts[0].date_start

                if running_contracts:
                    i.current_contract_start = running_contracts[0].date_start
                    i.current_contract_end = running_contracts[0].date_end
                    if running_contracts.filtered(lambda x: x.date_end == False):
                        i.fixed_term = False
                else:
                    i.last_employed = all_emp_contracts[0].date_end

    def _search_is_fixed_term(self, operator, value):
        non_expiring = self.sudo().env['hr.contract'].search(['&', ('state', 'in', ['open', 'pending']), ('date_end', '!=', False)])
        emp = []
        for i in non_expiring:
            emp.append(i.employee_id.id)
        
        if ((operator == '=') and (value == True)) or ((operator == '!=') and (value == False)):
            return [('id', 'in', emp)]
        else:
            return ['!', ('id', 'in', emp)]


    first_employed = fields.Date(string="First Assumption", compute='_compute_contract_info')
    last_employed = fields.Date(string="Left Since", compute='_compute_contract_info')

    current_contract_start = fields.Date(string="Current Contract Start", compute='_compute_contract_info')
    current_contract_end = fields.Date(string="Current Contract End", compute='_compute_contract_info')

    fixed_term = fields.Boolean(string="Fixed-Term", compute="_compute_contract_info", search="_search_is_fixed_term")

    is_subworker = fields.Boolean(string="Subcontracted Worker", default=False)

    active_contract = fields.Boolean(compute='compute_active_contract', store=True)

    @api.depends('contract_ids')
    def compute_active_contract(self):
        for i in self:
            if i.contract_ids.filtered(lambda x: x.state in ['open', 'pending']):
                i.active_contract = True
            else:
                i.active_contract = False


class EmployeeCategory(models.Model):
    _inherit = ['hr.employee.category']

    icon = fields.Binary(
        "Photo", attachment=True,
        help="This field holds an icon to be used as a badge on various reports.")


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    def _prepare_holidays_meeting_values(self):
        result = []
        company_calendar = self.env.company.resource_calendar_id
        for holiday in self:
            calendar = holiday.employee_id.resource_calendar_id or company_calendar
            meeting_values = {
                'name': holiday.display_name,
                'duration': holiday.number_of_days * (calendar.hours_per_day or HOURS_PER_DAY),
                'description': holiday.notes,
                'user_id': holiday.user_id.id,
                'start': holiday.date_from,
                'stop': holiday.date_to,
                'allday': False,
                'privacy': 'confidential',
                'event_tz': holiday.user_id.tz,
                'activity_ids': [(5, 0, 0)],
            }
            # Add the partner_id (if exist) as an attendee
            if holiday.user_id and holiday.user_id.partner_id:
                meeting_values['partner_ids'] = [
                    (4, holiday.user_id.partner_id.id)]
            result.append(meeting_values)
        return result