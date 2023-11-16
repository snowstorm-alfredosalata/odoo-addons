from odoo import api, fields, models, _
from odoo.addons.base.models.res_partner import _tz_get

from dateutil import relativedelta
import pytz

from collections import namedtuple
Range = namedtuple('Range', ['start', 'end'])

class HrAttendanceStructure(models.Model):
    _name = 'hr.attendance.structure'
    _description = "Attendance Structures"
    _order = 'sequence'

    sequence = fields.Integer('Sequence')
    name = fields.Char("Description", required=True)
    code = fields.Char("Code", required=True, limit=8)

    lines = fields.One2many('hr.attendance.structure.line', 'structure_id', "Structure Lines")

    tz = fields.Selection(
        _tz_get, string='Timezone', required=True,
        default=lambda self: self._context.get('tz') or self.env.user.tz or 'UTC',
        help="This field is used in order to define in which timezone the resources will work.")

    def _generate_intervals(self, date_start=False, date_end=False):
        if not date_start:
            date_start = fields.Datetime.now()
        
        date_computation_start = date_start.astimezone(pytz.timezone(self.tz or 'UTC')).replace(hour=0, minute=0, second=0, microsecond=0)

        if not date_end or date_end < date_start:
            date_end = date_start + relativedelta.relativedelta(days=1)

        current_line = 0
        current_day  = 0
        intervals = list()

        while True:
            if current_line >= len(self.lines):
                current_line = 0
                current_day += 1

            line = self.lines[current_line]
            line_start = date_computation_start.replace(hour=0, minute=0, second=0, microsecond=0) + relativedelta.relativedelta(days=current_day, hours=line.time_start)
            line_end   = date_computation_start.replace(hour=0, minute=0, second=0, microsecond=0) + relativedelta.relativedelta(days=current_day, hours=line.time_end)
            
            current_line += 1

            if line_end < date_start:
                continue

            intervals.append(
                (
                    line.reason_id.id, line.reason_extra_id.id,
                    Range(line_start, line_end)
                )
            )

            if line_end > date_end:
                return intervals
            

class HrAttendanceStructureLine(models.Model):
    _name = 'hr.attendance.structure.line'
    _description = "Attendance Structure Lines"

    structure_id = fields.Many2one('hr.attendance.structure', 'Structure', required=True, ondelete='cascade')

    time_start = fields.Float("Start", required=True)
    time_end = fields.Float("End", required=True)

    reason_id = fields.Many2one('hr.attendance.type', "Applied Reason", required=True, domain=[('att_type', '=', 'work')])
    reason_extra_id = fields.Many2one('hr.attendance.type', "Applied Reason for Extras", domain=[('att_type', '=', 'extra')], required=True)