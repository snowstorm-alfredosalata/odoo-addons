from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"


    qty_to_deliver = fields.Float('Quantità Residua', readonly=True)
    untaxed_amount_to_deliver = fields.Float('Imponibile Residuo', readonly=True)
    commitment_date = fields.Datetime('Data di Impegno', readonly=True)
    
    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['commitment_date'] = ", s.commitment_date as commitment_date"
        fields['qty_to_deliver'] = ", sum(greatest(l.product_uom_qty - l.qty_delivered, 0) / u.factor * u2.factor) as qty_to_deliver"
        fields['untaxed_amount_to_deliver'] = ", sum( l.price_unit * (greatest(l.product_uom_qty - l.qty_delivered, 0) / u.factor * u2.factor) ) as untaxed_amount_to_deliver"
        groupby += ', s.commitment_date'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)

    def name_get(self):
        res = []
        for sale in self:
            res.append(
                (sale.id, '%s - %s' % (sale.order_id.name, sale.product_id.display_name)))
        return res