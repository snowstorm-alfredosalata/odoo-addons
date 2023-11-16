# -*- coding: utf-8 -*-

import logging
import re

from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

try:
    from .api_client import OnedriveApiClient as Client
except Exception as error:
    # Exception is handled in the api_client itself
    _logger.error("API Client is not found: {}".format(error))

# 'openid' - to able to sign (under consideration whether it is really requried)
# 'Files.ReadWrite.All' - read and write in all files
# 'offline_access' - to receive refresh_token instead of one-hour durable
SCOPES = ['openid', 'Files.ReadWrite.All', 'offline_access']


class onedrive_client(models.AbstractModel):
    """
    The wrapper model for microsoftgraph library. It is used only for authentication purposes
    All sync methods are done within ir.attachment model, which directly apply to Client API
    """
    _name = "onedrive.client"
    _description = "OneDrive Client"

    @api.model
    def get_client(self, new_token_required=False):
        """
        Method to return instance of wrapped Onedrive API

        Args:
         * new_token_required - Bool - in case we authenticate for the first time we should not refresh token

        Methods:
         * refresh_token - with each apply we refresh token. It guarantees that even a single sync per 6 months
           would prolong session for the next 6 months

        Returns:
         * OnedriveApiClient instance with initiated token from system params
        """
        Config = self.env['ir.config_parameter'].sudo()
        client_id = Config.get_param('onedrive_client_id', '')
        onedrive_client_secret = Config.get_param('onedrive_client_secret', '')
        redirect_uri = Config.get_param('onedrive_redirect_uri', '')
        api_client = Client(client_id, onedrive_client_secret)
        token_dict_str = Config.get_param('onedrive_session', '')
        if token_dict_str and not new_token_required:
            token_dict = safe_eval(token_dict_str)
            token = api_client.refresh_token(redirect_uri=redirect_uri, refresh_token=token_dict.get("refresh_token"))
            api_client.set_token(token)
        return api_client

    @api.model
    def get_auth_url(self):
        """
        Get URL of authentification page
         1. Clean session, if new url is required

        Methods:
         * get_client
         * authorization_url of OnedriveApiClient instance

        Returns:
         * char - url of application to log in

        Extra info:
         * The response is received by the controller to /one_drive_token
         * Do not forget to configure backward url in Azure settings
        """
        Config = self.env['ir.config_parameter'].sudo()
        # 1
        Config.set_param('onedrive_session', '')
        onedrive_client = self.get_client(new_token_required=True)
        scope = SCOPES
        if safe_eval(Config.get_param('onedrive_sharepoint_sites', 'False')):
            scope.append("Sites.ReadWrite.All")
        redirect_uri = Config.get_param('onedrive_redirect_uri', '')
        auth_url = onedrive_client.authorization_url(redirect_uri, scope, state=None)
        _logger.info('Auth url for onedrive is retrieved: {}'.format(auth_url))
        return auth_url

    @api.model
    def create_onedrive_session(self, code=False):
        """
        Authenticates to OndDrive

        Args:
         * code - authorization code received

        Methods:
         * set_token - to apply correct token for OnedriveApiClient instance
         * exchange_code of OnedriveApiClient instance
        """
        api_client = self._context.get("client")
        if code:
            Config = self.env['ir.config_parameter'].sudo()
            redirect_uri = Config.get_param('onedrive_redirect_uri', '')
            client_secret = Config.get_param('onedrive_client_secret', '')
            onedrive_business = Config.get_param('onedrive_business', '')
            sharepoint = Config.get_param('onedrive_sharepoint_sites', '')
            try:
                token_dict = api_client.exchange_code(redirect_uri=redirect_uri, code=code)
                api_client.set_token(token_dict)
                Config.set_param('onedrive_session', token_dict)
                self._context.get("s_logger").info(u'Authentification to OneDrive is successfull'.format())
            except Exception as error:
                self._context.get("s_logger").error(u'Authentification to OneDrive failed. Reason: {}'.format(error))
                raise UserError("Can't authenticate to OneDrive")
            Config.set_param('cloud_client_state', 'confirmed')
        else:
            self._context.get("s_logger").error(u'No valid OneDrive code or client provided. Code: {}'.format(code))
            raise UserError("Can't authenticate to OneDrive")

    @api.model
    def search_drive_id(self):
        """
        Method to find drive_id in OneDrive of selected directory if it a business account or user drive instead
        Besides, we receive here "deltaURL"
        The result is saved to configs

        Methods:
         * get_site_id
         * get_site_drives
        """
        api_client = self._context.get("client")
        Config = self.env['ir.config_parameter'].sudo()
        sharepoint_sites = safe_eval(Config.get_param('onedrive_sharepoint_sites', 'False'))
        sharepoint_drive = Config.get_param('onedrive_sharepoint_drive', 'me')
        drive = 'me'
        if sharepoint_sites:
            try:
                site_id = self.get_site_id(api_client=api_client)
                drives = api_client.drives_list_o(site_id=site_id)
                for prop in drives["value"]:
                    if prop['name'] == sharepoint_drive:
                        drive = prop['id']
                        break
                else:
                    error_mes = u"SharePoint documents library - {} - is not found ".format(sharepoint_drive)
                    self._context.get("s_logger").error(error_mes)
                    raise UserError(error_mes)
            except Exception as error:
                error_mes = u"Sharepoint site library is not found. Reason: {}".format(error)
                self._context.get("s_logger").error(error_mes)
                raise UserError(error_mes)
        else:
            # For onedrive personal & business there is only a single drive
            try:
                drives = api_client.personal_drive_o()
                drive = drives.get("id")
            except Exception as error:
                error_mes = u"Drive is not found. Reason: {}".format(error)
                self._context.get("s_logger").error(error_mes)
                raise UserError(error_mes)
        Config.set_param('onedrive_drive_id', drive)
        self._context.get("s_logger").info(u"Set OneDrive active drive to {}".format(drive))

    @api.model
    def get_site_id(self, api_client):
        """
        The method to return sharepoint site id based on url and site name

        Args:
         * api_client - instance of OnedriveApiClient

        Methods:
         *  sharepoint_site_o of OnedriveApiClient instance

        Returns:
         * char
        """
        Config = self.env['ir.config_parameter'].sudo()
        base_url = Config.get_param('onedrive_sharepoint_base_url', '')
        # Need to replace extra params and the closing dash
        base_url = base_url.replace("http://","")
        base_url = base_url.replace("https://","")
        base_url = re.sub(r'(www.)(?!com)',r'',base_url)
        if base_url[-1] == '/':
            base_url = base_url[:len(base_url)-1]
        site_name = Config.get_param('onedrive_sharepoint_site_name', '')
        if site_name.find("/") == -1:
            site_name = "sites/{}".format(site_name)
        relative_path = "{}:/{}".format(base_url, site_name)
        site = api_client.sharepoint_site_o(path=relative_path)
        site_id = site.get("id")
        return site_id
