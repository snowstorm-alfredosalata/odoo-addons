# -*- coding: utf-8 -*-

from odoo import api, fields, models

class Visit(models.Model): 
    _name = 'visitor.visitor'
    _description = 'Visitor'
    _order = 'state asc, check_out desc, check_in desc'

    name = fields.Char(string='Motivo della Visita', required=True) 
    state = fields.Selection([
        ('draft', 'Bozza'),
        ('confirm', 'Autorizzata'),
        ('start', 'Check in fatto'),
        ('done', 'Check out fatto'),
        ('cancel', 'Annullato')
        ], string='Status', readonly=True, copy=False, default='draft')
    
    partner_id = fields.Many2one('res.partner', string='Contatto', readonly=True, states={'draft': [('readonly', False)]})

    visitor_name    = fields.Char(string='Visitatore',          required=True, readonly=True, states={'draft': [('readonly', False)]})
    visitor_company = fields.Char(string='Azienda',             required=True, readonly=True, states={'draft': [('readonly', False)]})
    visitor_phone   = fields.Char(string='Recapito Visitatore', required=True, readonly=True, states={'draft': [('readonly', False)]})

    accompanied_by = fields.Char(string='Accompagnatore', required=True, readonly=True, states={'draft': [('readonly', False)]})

    date_planned = fields.Date(string='Planned Date',  readonly=True, states={'draft': [('readonly', False)]}, required=True)

    check_in = fields.Datetime(string='Check in', readonly=True, 
        states={'confirm': [('readonly', False)]})
    check_out = fields.Datetime(string='Check Out', readonly=True, 
        states={'start': [('readonly', False)]})

    notes = fields.Text('Note')

    ## Buttons
    def action_cancel(self):
        self.write({'state': 'cancel'})
    
    def action_confirm(self):
        for i in self:
            if i.state == 'draft':
                i.write({'state': 'confirm'})

    def action_start(self):
        if not self.check_in:
            self.check_in = fields.Datetime.now()

        return self.write({'state': 'start'})

    def action_done(self):
        if not self.check_out:
            self.check_in = fields.Datetime.now()

        return self.write({'state': 'done',})

    @api.constrains('check_out')
    def _check_date_validity(self): 
        if(self.check_out < self.check_in): 
            raise models.ValidationError('Errore! Il Check-Out deve essere posteriore al check-in.')

    @api.onchange('check_in')
    def update_check_out(self):
        if((not self.check_out) or (self.check_in > self.check_out)):
            self.check_out = self.check_in