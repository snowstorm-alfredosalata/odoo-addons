from odoo import api, fields
from odoo.exceptions import ValidationError, AccessError, MissingError, UserError
from odoo.http import content_disposition, Controller, request, route
from odoo import tools
import json

import logging


class MESController(Controller):

    @route(['/kontrol/workcenter/<workcenter_id>/log'], type='http', auth='none', methods=['POST'], csrf=False)
    def workcenter_log_shot(self, redirect=None, workcenter_id=False, **post):
        if post.get('mode', False) == 'update_latest':
            request.env['mrp.workcenter'].sudo().browse(int(workcenter_id)).update_latest(**post)

        else:
            request.env['mrp.workcenter'].sudo().browse(int(workcenter_id)).log(fields.Datetime.now(), **post)

        response = request.make_response("True",{
            'Cache-Control': 'no-cache',
            'Content-Type': 'text/html; charset=utf-8',
            })
        return response

    @route(['/kontrol/workcenter/<workcenter_id>/get'], type='http', auth='none', methods=['GET'], csrf=False)
    def workcenter_get(self, redirect=None, workcenter_id=False):
        wc = request.env['mrp.workcenter'].sudo().browse(int(workcenter_id))
        wos = request.env['mrp.workorder'].sudo().search([('workcenter_id', '=', wc.id), ('state', '=', 'progress'), ('mes_ignore', '=', False)])
        
        data = {'id': wc.id, 'name': wc.name, 'orders': list()}

        for i in wos:
            last_loss = i.time_ids and i.time_ids[0]
            data['orders'].append({'id': i.id, 'time_cycle': i.operation_id.time_cycle_manual, 'last_loss_start': last_loss and last_loss.date_start.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT) or False, 'last_loss_loss_id': last_loss and last_loss.loss_id.id or False})

        response = request.make_response(json.dumps(data),{
            'Cache-Control': 'no-cache',
            'Content-Type': 'text/html; charset=utf-8',
            })
        return response

        
    @route(['/kontrol/workcenter/<workcenter_id>/record'], type='http', auth='none', methods=['POST'], csrf=False)
    def workcenter_record_production(self, redirect=None, workcenter_id=False, **post):
        wos = request.env['mrp.workorder'].sudo().search([('workcenter_id', '=', int(workcenter_id)), ('state', '=', 'progress'), ('mes_ignore', '=', False)])
        for wo in wos:
            wo.record_production()

        response = request.make_response("True",{
        'Cache-Control': 'no-cache',
        'Content-Type': 'text/html; charset=utf-8',
        })
        return response