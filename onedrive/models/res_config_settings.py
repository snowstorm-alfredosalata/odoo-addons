# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

PARAMS = (
    ('onedrive_client_id', str, ''),
    ('onedrive_client_secret', str, ''),
    ('onedrive_redirect_uri', str, 'http://localhost:8069/one_drive_token'),
    ('onedrive_business', safe_eval, False),
    ('onedrive_sharepoint_sites', safe_eval, False),
    ('onedrive_sharepoint_base_url', str, ''),
    ('onedrive_sharepoint_site_name', str, ''),
    ('onedrive_sharepoint_drive', str, 'Documents'),
    ('onedrive_drive_id', str, 'Documents'),
)


class res_config_settings(models.TransientModel):
    """
    Re-write to add OneDrive configuration settings
    """
    _inherit = "res.config.settings"

    onedrive_client_secret = fields.Char(
        string="App Secret Key",
    )
    onedrive_client_id = fields.Char(
        string="App Client ID",
    )
    onedrive_redirect_uri = fields.Char(
        string="Redirect URL",
        default='http://localhost:8069/one_drive_token',
        help="The same redirect url should be within your Onedrive app settings"
    )
    onedrive_business = fields.Boolean(
        string="OneDrive for business?",
    )
    onedrive_sharepoint_sites = fields.Boolean(
        string="Use sharepoint sites?",
    )
    onedrive_sharepoint_base_url = fields.Char(
        string="Sharepoint URL",
        help="""Sharepoint url should be of the type https://[URL]/
                The last '/' is required.
                Sitename should not be included into the url"""
    )
    onedrive_sharepoint_site_name = fields.Char(
        string="Sharepoint site",
        help="""
            SharePoint site should be either 'my_site_name' (in that case it is considered as 'sites/my_site_name')
            or 'sites/my_site_name'. Instead of 'sites' it might be 'teams', for example. It depends on your Sharepoint
            There should be no '/' at the beginning or at the end"""
    )
    onedrive_sharepoint_drive = fields.Char(
        string="Documents Library",
        help="""
            In SharePoint you might have a few documents libraries (drives). A standard one is 'Documents', but you
            might create another one. Within this document library, the 'Odoo' folder would be generated. After the
            first sync it is allowed to move the 'Odoo' folder within the same library, but not to others
        """,
        default='Documents',
    )
    onedrive_drive_id = fields.Char(
        string="Drive id in OneDrive",
        default='Documents',
    )

    @api.model
    def get_values(self):
        """
        Overwrite to add new system params
        """
        Config = self.env['ir.config_parameter'].sudo()
        res = super(res_config_settings, self).get_values()
        values = {}
        for field_name, getter, default in PARAMS:
            values[field_name] = getter(str(Config.get_param(field_name, default)))
        res.update(values)
        return res

    @api.model
    def set_values(self):
        """
        Overwrite to add new system params
        """
        Config = self.env['ir.config_parameter'].sudo()
        super(res_config_settings, self).set_values()
        for field_name, _, _ in PARAMS:
            value = getattr(self, field_name)
            Config.set_param(field_name, str(value))

    def action_login_to_onedrive(self):
        """
        The action to log in Microsoft Graph and confirm permissions

        Methods:
         * get_auth_url of onedrive.client to return target url

        Returns:
         * action of opening a page
        """
        auth_url = self.env["onedrive.client"].get_auth_url()
        res = {
            'name': 'OneDrive',
            'res_model': 'ir.actions.act_url',
            'type': 'ir.actions.act_url',
            'target': 'current',
            'url': auth_url
        }
        return res

    def action_reset(self):
        """
        The method to remove all data and objects related to onedrive

        Returns:
         * Refreshed configs
        """
        super(res_config_settings, self).action_reset()
        params, _, _ = zip(*PARAMS)
        params += ('onedrive_root_dir_id', 'onedrive_session', 'onedrive_delta_url')
        self._cr.execute('DELETE FROM ir_config_parameter WHERE key IN %s', (params,))

    def action_reconnect(self):
        """
        The method to reset configs state to drive without unlink of the most of configs except session

        Returns:
         * Refreshed configs
        """
        Config = self.env['ir.config_parameter'].sudo()
        Config.set_param('cloud_client_state', 'reconnect')

