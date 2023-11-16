# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval



class res_config_settings(models.TransientModel):
    _inherit = "res.config.settings"

    synced_model_ids = fields.Many2many(
        "sync.model",
        "sync_model_res_config_setting_rel_table",
        "sync_model_id",
        "res_config_setting_id",
        string="List of synced Odoo Models",
    )
    cloud_client_state = fields.Selection(
        [
            ('draft', 'Not Confirmed'),
            ('confirmed', 'Confirmed'),
            ('reconnect', 'Reconnect'),
        ],
        default='draft',
        string="State",
    )
    sync_logs = fields.Boolean(
        string="Log sync activities",
        help="""
            It would slow down the sync process, but you will have a chance to
            observe all uploads, downloads, unlink, move and remove activities as
            a list of logs
        """,
    )
    cloud_timeout = fields.Integer(string="Odoo Server Timeout (seconds)", default=900)

    @api.model
    def get_values(self):
        """
        Overwrite to add new system params
        """
        res = super(res_config_settings, self).get_values()
        Config = self.env['ir.config_parameter'].sudo()
        to_sync_model_ids =  safe_eval(Config.get_param("odoo_models_to_sync", "[]"))
        to_sync_model_real_ids = self.sudo().env["sync.model"].search([("id", "in", to_sync_model_ids)])
        cloud_client_state = Config.get_param("cloud_client_state", "draft")
        sync_logs = safe_eval(Config.get_param("sync_logs", "False"))
        cloud_timeout = int(Config.get_param("cloud_timeout", "900"))
        values = {
            "synced_model_ids": [(6, 0, to_sync_model_real_ids.ids)],
            "cloud_client_state": cloud_client_state,
            "sync_logs": sync_logs,
            "cloud_timeout": cloud_timeout,
        }
        res.update(values)
        return res

    @api.model
    def set_values(self):
        """
        Overwrite to add new system params
        """
        super(res_config_settings, self).set_values()
        Config = self.env['ir.config_parameter'].sudo()
        Config.set_param("odoo_models_to_sync", self.synced_model_ids.ids)
        Config.set_param("cloud_client_state", self.cloud_client_state)
        Config.set_param("sync_logs", self.sync_logs)
        Config.set_param("cloud_timeout", self.cloud_timeout)

    def action_sync_to(self):
        """
        The method to trigger attachments upload to Cloud Client

        Method:
         * method_direct_trigger of ir.cron
        """
        cron_id = self.env.ref("cloud_base.syncronize_attachments_with_cloud")
        cron_id.method_direct_trigger()

    def action_sync_from(self):
        """
        The method to trigger attachments download from Cloud Client

        Methods:
         * method_direct_trigger of ir.cron
        """
        cron_id = self.env.ref("cloud_base.cron_update_from_onedrive")
        cron_id.method_direct_trigger()

    def action_reset(self):
        """
        The method to reset all cloud client settings
        """
        self._cr.execute("DELETE FROM sync_model")
        self._cr.execute("DELETE FROM sync_object")
        mis_conf = ("odoo_models_to_sync", "cloud_client_state")
        self._cr.execute('DELETE FROM ir_config_parameter WHERE key IN %s', (mis_conf,))
