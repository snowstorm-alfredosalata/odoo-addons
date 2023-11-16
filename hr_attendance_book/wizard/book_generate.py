# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AttendanceBookGeneration(models.TransientModel):
    _name = "hr.attendance.book.generate"
    _description = "Attendance Generation Wizard"

    def _compute_books(self):
        self.book_ids = self.env['hr.attendance.book'].browse(self._context.get('active_ids', []))

    book_ids = fields.Many2many('hr.attendance.book', compute=_compute_books)
    state = fields.Selection([('draft', 'Draft'),('done','Done')], 'Status', default="draft")

    def generate(self):
        book_ids = self.env['hr.attendance.book'].generate_books()
        self.state = 'done'

        return {
            'context': self.with_context(active_ids=book_ids.ids).env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def view_generated(self):
        return {
            'name': _("Generated Books"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [("id", "in", self.book_ids.ids)],
            'res_model': 'hr.attendance.book',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }