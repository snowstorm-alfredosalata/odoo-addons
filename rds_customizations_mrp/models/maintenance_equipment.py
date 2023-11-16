# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

from odoo import api, fields, models, tools


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    owner_id = fields.Many2one('res.partner', 'Proprietario')
    owner_ref = fields.Char('Riferimento Propietario')

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        equipment_ids = []
        if name:
            equipment_ids = self._search(['|', ('name', '=', name), ('serial_no', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid)
        if not equipment_ids:
            equipment_ids = self._search(['|', ('name', operator, name), ('serial_no', operator, name)] + args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(equipment_ids).name_get()

    def name_get(self):
        result = []
        for record in self:
            if record.name and record.serial_no:
                result.append((record.id, ("%s: " %  record.serial_no) + record.name))
            if record.name and not record.serial_no:
                result.append((record.id, record.name))
        return result


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    partner_id = fields.Many2one('res.partner', "Assegnato a Fornitore")
    
    workcenter_id = fields.Many2one('mrp.workcenter', "Centro di Lavoro", related="equipment_id.workcenter_id", store=True)