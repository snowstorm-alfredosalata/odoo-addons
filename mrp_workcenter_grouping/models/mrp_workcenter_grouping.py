# $$LICENSE_BRIEF$$

from odoo import models, fields, api, _

# TODO: Implement these


class MrpPlant(models.Model):
    _description = """
    Allows mapping workcenters to a certain plant.
    Used mainly for grouping purposes on reports.
    """
    _name = 'mrp.plant'

    name = fields.Char("Plant", required=True)

    workcenter_ids = fields.One2many('mrp.workcenter', 'plant_id', "Workcenters")

    is_editable = fields.Boolean(compute='_compute_is_editable')
    
    def _compute_is_editable(self):
        for record in self:
            workorders = self.env['mrp.workorder'].search([('workcenter_id', 'in', record.workcenter_ids.ids)])
            productivity_logs = self.env['mrp.workcenter.productivity'].search([('workcenter_id', 'in', record.workcenter_ids.ids)])

            record.is_editable = (len(workorders) + len(productivity_logs) == 0)


class MrpDepartment(models.Model):
    _description = """
    Allows mapping workcenters to a certain department.
    Used mainly for grouping purposes on reports.
    """
    _name = 'mrp.department'
    

    name = fields.Char("Department", required=True)

    plant_id = fields.Many2one('mrp.plant', "Plant", required=True)
    
    workcenter_ids = fields.One2many('mrp.workcenter', 'department_id', "Workcenters")

    is_editable = fields.Boolean(compute='_compute_is_editable')
    
    def _compute_is_editable(self):
        for record in self:
            workorders = self.env['mrp.workorder'].search([('workcenter_id', 'in', record.workcenter_ids.ids)], limit=1)
            productivity_logs = self.env['mrp.workcenter.productivity'].search([('workcenter_id', 'in', record.workcenter_ids.ids)], limit=1)

            record.is_editable = (len(workorders) + len(productivity_logs) == 0)


class MrpWorkcenterGroup(models.Model):
    _description = """
    Allows mapping groups of workcenter that usually (but not necessarily always)
    concur to the processing of the same Production order at the same time. 
    For instance, it might group several assembly stations in a single assembly line, or 
    a group of machines working on the same part in series with automated feeding.
    """
    _name = 'mrp.workcenter.group'

    name = fields.Char("Workcenter Group", required=True)

    plant_id = fields.Many2one('mrp.plant', "Plant", required=True)
    department_id = fields.Many2one('mrp.department', "Department", required=True)

    workcenter_ids = fields.One2many('mrp.workcenter', 'group_id', "Workcenters")

    is_editable = fields.Boolean(compute='_compute_is_editable')
    
    def _compute_is_editable(self):
        for record in self:
            workorders = self.env['mrp.workorder'].search([('workcenter_id', 'in', record.workcenter_ids.ids)], limit=1)
            productivity_logs = self.env['mrp.workcenter.productivity'].search([('workcenter_id', 'in', record.workcenter_ids.ids)], limit=1)

            record.is_editable = (len(workorders) + len(productivity_logs) == 0)