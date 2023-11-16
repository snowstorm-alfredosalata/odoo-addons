# -*- coding: utf-8 -*-

import logging
import werkzeug

from odoo.http import Controller, route, request

_logger = logging.getLogger(__name__)


class one_drive_token(Controller):

    @route('/one_drive_token', type='http', auth='user', website='False')
    def login_to_onedrive(self, code=False, session_state=False):
        """
        Controller that handles incoming token from Microsoft graph

        Methods:
         * create_onedrive_session of onedrive.client
         * search_drive_id of onedrive.clients

        Returns:
         * configs view
        """
        ctx = request.env.context.copy()
        new_ctx = request.env["ir.attachment"]._return_client_context()
        ctx.update(new_ctx)
        request.env['onedrive.client'].with_context(ctx).create_onedrive_session(code=code)
        request.env['onedrive.client'].with_context(ctx).search_drive_id()
        config_action = request.env.ref('cloud_base.cloud_config_action')
        url = "/web#view_type=form&model=res.config.settings&action={}".format(
            config_action and config_action.id or ''
        )
        return werkzeug.utils.redirect(url)
