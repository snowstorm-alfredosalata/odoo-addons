from odoo import fields, models, api
from dateutil import relativedelta

from odoo.exceptions import ValidationError
import pytz

def safe_localize(dt, tz):
    if not dt:
        return dt

    return pytz.utc.localize(dt).astimezone(pytz.timezone(tz))


class MrpAndon(models.Model):
    _name = 'mrp.andon'
    _description = 'Informative Panel / Andon'
    
    name = fields.Char("Andon Name", required=True)
    workcenter_ids = fields.Many2many('mrp.workcenter', 'mrp_workcenter_mrp_andon_rel', string='Centri di Lavoro')
    
    tag = fields.Char("Andon Tag", default='workcenter_productivity_timetable')
    context = fields.Text("Added Context")

    action_id = fields.Many2one('ir.actions.client', "Client Action", readonly=True, copy=False)
    menu_id = fields.Many2one('ir.ui.menu', "Menu Item",  readonly=True, copy=False)

    published = fields.Boolean(copy=False)
    fullscreen = fields.Boolean()

    debug = fields.Boolean()
    auto_refresh = fields.Float()

    def get_data(self, options={}):
        now = fields.Datetime.now()
        offset = options.get('offset', 0)
        from_params, to_params = {}, {}

        if options.get('period', False) == 'weeks':
            from_params['weeks'] = offset + 1
            to_params['weeks'] = offset
            #from_params['weekday'] = 6
            #to_params['weekday'] = 6
        else:
            from_params['days'] = offset + 1
            to_params['days'] = offset

        from_date = now - relativedelta.relativedelta(**from_params)
        to_date = now - relativedelta.relativedelta(**to_params)

        wcs = list()
        for wc in self.workcenter_ids.with_context(oee_date_from=from_date, oee_date_to=to_date):
            line = {
                'id': wc.id,
                'name': wc.name,
                'code': wc.code,
                'oee': wc.oee,
                'working_state': wc.working_state,
                'loss_ids': [{'date_start': safe_localize(x.date_start, self.env.user.tz), 
                              'date_end': safe_localize(x.date_end or to_date, self.env.user.tz),
                              'loss_id': x.loss_id.id, 
                              'color': x.loss_id.loss_id.color} 
                            for x in self.env['mrp.workcenter.productivity'].search([
                                '&',
                                    '&',
                                        ('workcenter_id', '=', wc.id),
                                        ('date_start', '<=', to_date),
                                    '|', 
                                        ('date_end', '>=', from_date),
                                        ('date_end', '=', False)
                                ], order='date_start desc')]
            }
            
            if len(line['loss_ids']) > 0:
                wcs.append(line)

        return {'workcenter_ids': wcs, 
                'debug': self.debug, 
                'from_date': safe_localize(from_date, self.env.user.tz), 
                'to_date': safe_localize(to_date, self.env.user.tz),                 
                'legend': [{'name': x.name,
                            'color': x.color} 
                            for x in self.env['mrp.workcenter.productivity.loss.type'].search([])]}

    def btn_show_andon(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx['andon_id'] = self.ids[0]
        return {
            'type': 'ir.actions.client',
            'name': "Andon: %s" % self.name,
            'tag': 'mrp_workcenter_kiosk',
            'context': ctx,
        }

    def btn_update_andon(self):
        self.ensure_one()
        ctx = eval(self.context) or {}
        ctx['andon_id'] = self.ids[0]

        self.sudo().action_id.context = str(ctx)
        self.sudo().action_id.tag = self.tag

    def btn_activate(self):
        self.ensure_one()

        ActClient = self.sudo().env['ir.actions.client']
        MenuItem = self.sudo().env['ir.ui.menu']
        parent = self.env.ref('odoo_kontrol.mrp_open_andons')

        ctx = eval(self.context) or {}
        ctx['andon_id'] = self.ids[0]

        if not self.action_id:
            self.action_id = ActClient.create({
                    'name': self.name,
                    'type': 'ir.actions.client',
                    'context': str(ctx),
                    'tag': self.tag,
                    'target': self.fullscreen and 'fullscreen' or False
                })


        if self.menu_id:
            self.sudo().menu_id.unlink()
            self.published = False

        else:
            self.menu_id = MenuItem.create({
                'name': self.name,
                'parent_id': parent.id,
                'action': 'ir.actions.client,%d' % (self.action_id.id)
            })
            self.published = True

    @api.model
    def get_html(self, andon_id=False, options={}):
        res = dict()
        res['report_type'] = 'html'
        res['report_structure'] = 'all'
        res['andon_id'] = andon_id
        res['html'] = self.env.ref('odoo_kontrol.report_productivity_timetable').render({'data': res})

        andon = self.browse(andon_id)
        options['auto_refresh'] = andon.auto_refresh

        res['graph'] = self.browse(andon_id).get_data(options)
        res['options'] = options
        return res