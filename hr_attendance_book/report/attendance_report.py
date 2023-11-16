# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class AttendanceReport(models.Model):
    _name = "hr.attendance.report"
    _description = "Attendance Analysis Report"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    date = fields.Date("Date", readonly=True)
    reason_id = fields.Many2one('hr.attendance.type', "Reason")
    att_type = fields.Selection([
        ('work', 'Attendance'),
        ('extra', 'Extra Attendance'),
        ('hol', 'Holiday'),
        ('absn', 'Absence')
        ], 'Attendance Type')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    qty = fields.Float("Quantity")

    def _query(self, with_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            min(x.day_id) as id,
            x.date as date,
            x.att_type as att_type,
            x.reason_id as reason_id,
            x.employee_id as employee_id,
            sum(x.qty) as qty
        """

        from_ = """
                (
        SELECT one.id AS day_id, wb.employee_id, one.workbook_id, one.date, tp.att_type, one.reason_1 AS reason_id, qty_1 AS qty
            FROM hr_attendance_day one 
            LEFT JOIN hr_attendance_type tp ON tp.id = one.reason_1
            LEFT JOIN hr_attendance_book wb ON wb.id = one.workbook_id
            WHERE one.reason_1 IS NOT NULL
        UNION ALL

        SELECT two.id AS day_id, wb.employee_id, two.workbook_id, two.date, tp.att_type, two.reason_2 AS reason_id, two.qty_2 AS qty
            FROM hr_attendance_day two
            LEFT JOIN hr_attendance_type tp ON tp.id = two.reason_2
            LEFT JOIN hr_attendance_book wb ON wb.id = two.workbook_id
            WHERE two.reason_2 IS NOT NULL
        UNION ALL
        
        SELECT three.id AS day_id, wb.employee_id, three.workbook_id, three.date, tp.att_type, three.reason_3 AS reason_id, three.qty_3 AS qty
            FROM hr_attendance_day three 
            LEFT JOIN hr_attendance_type tp ON tp.id = three.reason_3
            LEFT JOIN hr_attendance_book wb ON wb.id = three.workbook_id
            WHERE three.reason_3 IS NOT NULL
        UNION ALL

        SELECT four.id AS day_id, wb.employee_id, four.workbook_id, four.date, tp.att_type, four.reason_4 AS reason_id, four.qty_4 AS qty
            FROM hr_attendance_day four 
            LEFT JOIN hr_attendance_type tp ON tp.id = four.reason_4
            LEFT JOIN hr_attendance_book wb ON wb.id = four.workbook_id
            WHERE four.reason_4 IS NOT NULL
                ) x
        """

        groupby_ = """
            x.date,
            x.att_type,
            x.reason_id,
            x.employee_id
        """

        return '%s (SELECT %s FROM %s GROUP BY %s)' % (with_, select_, from_, groupby_)

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))