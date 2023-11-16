# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp

class MrpWorkcenterProductivityLossType(models.Model):
    _inherit = "mrp.workcenter.productivity.loss.type"
    _rec_name = 'name'

    @api.depends('name')
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, rec.name))
        return result
    
    name = fields.Char("Categoria", required="True")
    loss_type = fields.Selection(string="Tipo Causale", selection_add=[('excluded', 'Escluso da OEE'),('undefined_loss', 'Fermo Generico'),('scrap', 'Scarto')])
    color = fields.Char("Colore su Grafici")

class MrpWorkcenterProductivityLoss(models.Model):
    _inherit = "mrp.workcenter.productivity.loss"

    loss_id = fields.Many2one(string="Macrocausale", domain=([]))
    color = fields.Char("Colore su Grafici", related="loss_id.color")

class MrpWorkcenterProductivityTimestamp(models.Model):
    _name = "mrp.workcenter.productivity.timestamp"
    _description = "MRP Productivity Log Timestamp"
    _order = "timestamp desc"

    timestamp = fields.Datetime("Data")
    productivity_log_id = fields.Many2one('mrp.workcenter.productivity', ondelete='cascade')

class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    loss_id = fields.Many2one(string="Causale")
    loss_id_loss_id = fields.Many2one('mrp.workcenter.productivity.loss.type', string='Macrocausale', store=True, readonly=True, related='loss_id.loss_id')
    loss_type = fields.Selection(string="Tipo Causale")

    timestamp_ids = fields.One2many('mrp.workcenter.productivity.timestamp', 'productivity_log_id', "Cicli")

    qty_produced = fields.Float(string="Quantità Prodotta", digits=dp.get_precision('Product Unit of Measure'))
    
    time_cycle = fields.Float(string="Tempo Ciclo Nominale",    group_operator="avg", compute="_compute_efficiency", store=True)
    time_cycle_real = fields.Float(string="Tempo Ciclo Reale",  group_operator="avg", compute="_compute_efficiency", store=True)

    productive_duration = fields.Float(string="Produttività Reale", compute="_compute_efficiency", store=True)


    oee_mode = fields.Selection(string="Calcolo OEE", selection=[('standard', 'Standard'),
                                                                 ('quantity', 'Quantità Prodotte'),
                                                                 ('timestamp', 'Cicli Effettuati')],
                                                                 related='workcenter_id.oee_mode')

    @api.depends('loss_type', 'workorder_id', 
                 'workorder_id.operation_id', 'workorder_id.operation_id.time_cycle', 
                 'workcenter_id', 'workcenter_id.oee_mode', 
                 'qty_produced', 'duration', 'date_end')
    def _compute_efficiency(self):
        for i in self:
            if not i.workorder_id:
                continue
                
            i.time_cycle = i.workorder_id.operation_id.time_cycle

            if i.loss_type != 'productive':
                i.productive_duration = 0

            elif i.oee_mode == 'standard':
                i.productive_duration = i.duration

            elif i.oee_mode == 'quantity':
                if i.qty_produced == 0:
                    i.productive_duration = 0
                    i.time_cycle = 0
                    continue

                i.productive_duration = i.qty_produced * i.time_cycle / i.workorder_id.production_id.bom_id.product_qty
                i.time_cycle_real     = i.duration * i.workorder_id.production_id.bom_id.product_qty / i.qty_produced

            elif i.oee_mode == 'timestamp':
                if len(i.timestamp_ids) == 0:
                    i.productive_duration = 0
                    i.time_cycle = 0
                    continue

                i.productive_duration = len(i.timestamp_ids) * i.time_cycle
                i.time_cycle_real     = i.duration / len(i.timestamp_ids)