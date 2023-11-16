# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

import base64
import zipfile
import io
import logging
import re
import copy

from datetime import date, datetime
from lxml import etree

from odoo import api, fields, models, _
from odoo.tools import float_repr
from odoo.exceptions import UserError, ValidationError
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.tests.common import Form


_logger = logging.getLogger(__name__)

DEFAULT_FACTUR_ITALIAN_DATE_FORMAT = '%Y-%m-%d'


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res['invoiced_move_ids'] = [
            (6, 0, self.move_ids.filtered(lambda x: (x.state == 'done' and (not x.invoice_line_id))).ids)
        ]
        
        return res

class StockMove(models.Model):
    _inherit = 'stock.move'

    invoice_line_id = fields.Many2one('account.move.line', 'Invoice Line', copy=False)
    l10n_it_ddt_id = fields.Many2one('l10n_it.ddt', 'Transport Document', related="picking_id.l10n_it_ddt_id", store=False)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def compute_ddt_ids(self):
        for i in self:
            i.l10n_it_ddt_ids = i.invoiced_move_ids.mapped('l10n_it_ddt_id')

    l10n_it_ddt_ids = fields.One2many('l10n_it.ddt', string='Transport Documents', compute=compute_ddt_ids, store=False)

    invoiced_move_ids = fields.One2many('stock.move', 'invoice_line_id', 'Invoiced Move')

class AccountMove(models.Model):
    _inherit = 'account.move'

    def compute_ddt_ids(self):
        for i in self:
            i.l10n_it_ddt_ids = i.invoice_line_ids.mapped('l10n_it_ddt_ids')

    l10n_it_ddt_ids = fields.Many2many('l10n_it.ddt', string='Transport Documents', compute=compute_ddt_ids, store=False)

    def get_ddt_data(self): 
    
        dati_ddt = list()

        class riga_ddt():
            name = None
            date = None
            line_indexes = None
        
        idx = 1
        for line in self.invoice_line_ids:
            line.sequence = idx
            idx += 1

        for ddt in self.l10n_it_ddt_ids:
            if ddt.picking_type_code != 'outgoing':
                continue
            
            ddt_object = riga_ddt()
            
            ddt_object.name = ddt.name
            ddt_object.date = ddt.date
            ddt_object.line_indexes = self.invoice_line_ids.filtered(lambda x: ddt.id in x.l10n_it_ddt_ids.ids).mapped('sequence')
            dati_ddt.append(ddt_object)
        
        return dati_ddt

    