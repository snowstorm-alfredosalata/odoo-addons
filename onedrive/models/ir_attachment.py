# -*- coding: utf-8 -*-

import base64

from odoo import api, fields, models, registry

from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools.safe_eval import safe_eval

from odoo.addons.cloud_base.models.ir_attachment import check_allowed_mimetypes


def mkdir(client, drive, parent, name):
    """
    Create a folder on Onedrive

    Args:
     * client -  instance of OnedriveApiClient
     * drive - Drive object id
     * parent - DriveItem object id (or False)
     * name - char - new folder name

    Methods:
     * create_folder_o of OnedriveApiClient

    Returns:
     * char - DriveItem id of created folder

    Extra info:
     * We do not care for the duplicated names, since the Microsoft Graph Api cares for that
     * We do not remove illegal characters here, since they are removed already in sync.object and sync.model, while
       Odoo is always Odoo
    """
    parent = parent or 'root'
    res = client.create_folder_o(drive_id=drive, folder_name=name, parent=parent)
    res_id = res.get("id")
    return res_id


class ir_attachment(models.Model):
    """
    For onedrive we do not need path. That's why we put everywhere name instead
    """
    _inherit = "ir.attachment"

    cloud_key = fields.Char(string="OneDrive ID") #just to rename the field

    @api.model
    def _return_client_context(self):
        """
        The method to return necessary to client context (like session, root directory, etc.)

        Returns:
         * dict
        """
        with_context_dict = super(ir_attachment, self)._return_client_context()
        client = self.env['onedrive.client'].get_client()
        Config = self.env['ir.config_parameter'].sudo()
        drive_id = Config.get_param('onedrive_drive_id', 'Documents')
        if client and drive_id:
            with_context_dict.update({
                "client": client,
                "drive_id": drive_id,
            })
        else:
            mes = u"OneDrive Services are not available"
            with_context_dict.get("s_logger").error(mes)
            raise UserError(mes)
        return with_context_dict

    @api.model
    def _check_token_expiration(self):
        """
        The method to check whether token is already expired and if yes, refresh it
        """
        api_client = self._context.get("client")
        if api_client.exprires_in <= fields.Datetime.now():
            Config = self.env['ir.config_parameter'].sudo()
            token_dict_str = Config.get_param('onedrive_session', '')
            token_dict = safe_eval(token_dict_str)
            redirect_uri = Config.get_param('onedrive_redirect_uri', '')
            token = api_client.refresh_token(redirect_uri=redirect_uri, refresh_token=token_dict.get("refresh_token"))
            api_client.set_token(token)

    @api.model
    def _find_or_create_root_directory(self):
        """
        Method to return root directory name and id (create if not yet)

        Methods:
         * get_drive_item_o of client
         * mkdir
         * _check_token_expiration

        Returns:
         * key, name - name of folder and key in client
         * False if failed
        """
        self._check_token_expiration()
        try:
            client = self._context.get("client")
            drive = self._context.get("drive_id")
            Config = self.env['ir.config_parameter'].sudo()
            res_id = Config.get_param('onedrive_root_dir_id', '')
            if res_id:
                try:
                    #in try, since the folder might be removed in meanwhile
                    client.get_drive_item_o(drive_id=drive, drive_item_id=res_id).get("id")
                except Exception as error:
                    if type(error).__name__ == "NotFound":
                        res_id = False
                        self._context.get("s_logger").warning(
                            u"The root directory 'Odoo' has been removed from Onedrive. Creating a new one".format()
                        )
                    else:
                        res = False, False
                        self._context.get("s_logger").error(
                            u"The root directory 'Odoo': Unexpected Error. Reason: {}".format(error)
                        )
                        return res
            if not res_id:
                res_id = mkdir(client, drive, False, "Odoo")
                Config.set_param('onedrive_root_dir_id', res_id)
                Config.set_param('onedrive_delta_url', '')
                self._context.get("s_logger").debug(u"The root directory 'Odoo' is created in OneDrive".format())
            res = res_id, "Odoo"
        except Exception as error:
            res = False, False
            self._context.get("s_logger").error(
                u"The root directory 'Odoo' can't be created in OneDrive. Reason: {}".format(error)
            )
        return res

    @api.model
    def _create_folder(self, folder_name, parent_folder_key, parent_folder_path):
        """
        Method to create folder in clouds

        Args:
         * folder_name - name of created folder
         * parent_folder_key - ID of parent folder in client
         * parent_folder_path - path of parent folder

        Methods:
         * mkdir
         * _check_token_expiration()

        Returns:
         * key, path or False, False if failed
        """
        self._check_token_expiration()
        try:
            client = self._context.get("client")
            drive = self._context.get("drive_id")
            res = mkdir(client, drive, parent_folder_key, folder_name), folder_name
            self._context.get("s_logger").debug(u"The folder {} is created in OneDrive".format(folder_name))
        except Exception as error:
            res = False, False
            self._context.get("s_logger").error(
                u"The folder {} can't be created in OneDrive. Reason: {}".format(folder_name, error)
            )
        return res

    def _get_folder(self, folder_id):
        """
        Method to get folder in clouds

        Args:
         * folder_id - sync.model or sync.object
         * False if failed

        Methods:
         * get_drive_item_o
         * _check_token_expiration()

        Returns:
         * dict of values including 'url'
        """
        self._check_token_expiration()
        res = False
        try:
            client = self._context.get("client")
            drive = self._context.get("drive_id")
            if folder_id.key:
                # 1
                res = client.get_drive_item_o(drive_id=drive, drive_item_id=folder_id.key)
            if res:
                res = {
                    "res_id": res.get("id"),
                    "url": res.get("webUrl"),
                    "filename": res.get("name"),
                    "path": res.get("name"),
                }
        except Exception as error:
            res = False
            self._context.get("s_logger").error(
                u"The folder {} can't be found in OneDrive. Reason: {}".format(folder_id.name, error,)
            )
        return res

    @api.model
    def _update_folder(self, folder_id, new_folder_name):
        """
        Method to update folder in clouds

        Args:
         * folder_id - sync.model or sync.object object
         * new_folder_name - new name of folder

        Methods:
         * move_or_update_item_o of client
         * _check_token_expiration()

        Returns:
         * key, path or False, False if failed
        """
        self._check_token_expiration()
        try:
            client = self._context.get("client")
            drive = self._context.get("drive_id")
            result = client.move_or_update_item_o(
                drive_id=drive,
                drive_item_id=folder_id.key,
                new_parent=False,
                new_name=new_folder_name,
            )
            res = result.get("id"), new_folder_name
            self._context.get("s_logger").debug(
                u"The folder {} is updated in OneDrive to {}".format(folder_id.name, new_folder_name)
            )
        except Exception as error:
            res = False, False
            self._context.get("s_logger").error(
                u"The folder {} can't be updated in OneDrive to {}. Reason: {}".format(
                    folder_id.name,
                    new_folder_name,
                    error,
                )
            )
        return res

    @api.model
    def _move_folder(self, folder_id, new_parent_key, new_parent_path):
        """
        Method to move folder in clouds to a different parent

        Args:
         * folder_id - sync.model or sync.object object
         * new_parent_key - new parent folder key
         * new_parent_path - new parent folder path

        Methods:
         * move_or_update_item_o of client
         * _check_token_expiration()

        Returns:
         * key, path or False, False if failed
        """
        self._check_token_expiration()
        try:
            client = self._context.get("client")
            drive = self._context.get("drive_id")
            result = client.move_or_update_item_o(
                drive_id=drive,
                drive_item_id=folder_id.key,
                new_parent=new_parent_key,
                new_name=False,
            )
            res = result.get("id"), folder_id.name
            self._context.get("s_logger").debug(
                u"The folder {} is moved in OneDrive from {} to {}".format(
                    folder_id.name,
                    folder_id.path,
                    new_parent_path,
                )
            )
        except Exception as error:
            res = False, False
            self._context.get("s_logger").error(
                u"The folder {} can't be moved in OneDrive from {} to {}. Reason: {}".format(
                    folder_id.name,
                    folder_id.path,
                    new_parent_path,
                    error,
                )
            )
        return res

    @api.model
    def _remove_folder(self, folder_id):
        """
        Method to move folder in clouds to a different parent
        1. "Item not found" error is fine, since nothing to unlink

        Args:
         * folder_id - sync.model or sync.object object

        Methods:
         * delete_file_o of client
         * _check_token_expiration()

        Returns:
         * True or False if failed
        """
        self._check_token_expiration()
        try:
            client = self._context.get("client")
            drive = self._context.get("drive_id")
            result = client.delete_file_o(
                drive_id=drive,
                drive_item_id=folder_id.key,
            )
            res = True
            self._context.get("s_logger").debug(u"The folder {} is deleted in OneDrive".format(folder_id.name,))
        except Exception as error:
            if type(error).__name__ == "NotFound":
                # 1
                res = True
                self._context.get("s_logger").warning(
                    u"The folder {} is not deleted in OneDrive since it has been already deleted before".format(
                        folder_id.name,
                    )
                )

            else:
                res = False
                self._context.get("s_logger").error(
                    u"The folder {} can't be deleted in OneDrive. Reason: {}".format(folder_id.name, error)
                )
        return res

    @api.model
    def _return_child_items(self, folder_id, key=False, path=False):
        """
        Method to return child items of this folder
         1. If folder was removed, all its children were removed as well

        Args:
         * folder_id - sync.model or sync.object object
         * key - key of a folder (used if no folder)
         * path -  path of a folder (used if no folder)

        Methods:
         * get_drive_item_o of client
         * children_items_o of client
         * _check_token_expiration()

        Returns:
         * list of of child dicts including name, id, webUrl, path
         * None if error
        """
        self._check_token_expiration()
        try:
            client = self._context.get("client")
            drive = self._context.get("drive_id")
            drive_item_id = folder_id and folder_id.key or key
            res = client.children_items_o(
                drive_id=drive,
                drive_item_id=drive_item_id,
            )
            # to make compatible with cloud_base
            for child in res:
                child.update({"path": child.get("name")})
        except Exception as error:
            if type(error).__name__ == "NotFound":
                # 1
                res = []
            else:
                res = None
                self._context.get("s_logger").error(
                    u"Failed to find a folder {} in OneDrive. Reason: {}".format(folder_id, error)
                )
        return res

    def _send_attachment_to_cloud(self, folder_id):
        """
        Method to send attachment to cloud AND to receive item dict
         1. We are to the case of update from cloud

        Args:
         * folder_id - sync.object or sync.model object

        Methods:
         * _normalize_name - to remove illegal characters (side-effect: name would be unique)
         * get_drive_item_o of client
         * upload_large_file_o of client
         * _check_token_expiration()

        Returns:
         * dict of res_id, url, name, path
         * False if method failed

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        self._check_token_expiration()
        res = False
        try:
            client = self._context.get("client")
            drive = self._context.get("drive_id")
            if self.cloud_key:
                # 1
                res = client.get_drive_item_o(drive_id=drive, drive_item_id=self.cloud_key)
            else:
                name = self._normalize_name()
                content = base64.urlsafe_b64decode(self.datas)
                file_size = self.file_size
                if file_size <= 62910000000: # at the moment method doesn't split files into items
                    res = client.upload_large_file_o(drive_id=drive, folder_name=folder_id.key, file_name=name,
                                                     content=content, file_size=file_size)
                    self._context.get("s_logger").debug(
                        u"The file {} is uploaded in OneDrive to {}".format(self.name, folder_id.name)
                    )
                else:
                    self._context.get("s_logger").error(
                        u"The file {} can't be uploaded in OneDrive to {}. Reason: its size is more than 60Mib".format(
                            self.name,
                            folder_id.name,
                        )
                    )
            if res:
                res = {
                    "res_id": res.get("id"),
                    "url": res.get("webUrl"),
                    "filename": res.get("name"),
                    "path": res.get("name"),
                }
        except Exception as error:
            res = False
            self._context.get("s_logger").error(
                u"The file {} ({}) can't be taken / uploaded in OneDrive. Reason: {}".format(self.name, self.id, error)
            )
        return res

    def _upload_attachment_from_cloud(self):
        """
        Method to upload a file from cloud

        Methods:
         * download_file_o
         * _check_token_expiration()

        Returns:
         * binary
         * False if method failed
        """
        self.ensure_one()
        self._check_token_expiration()
        res = False
        try:
            client = self._context.get("client")
            drive = self._context.get("drive_id")
            result = client.download_file_o(drive_id=drive, drive_item=self.cloud_key)
            res = base64.b64encode(result)
        except Exception as error:
            res = False
            self._context.get("s_logger").error(u"Failed to download a file {},{} from OneDrive. Reason: {}".format(
                self.name, self.id, error,
            ))
        return res

    def _move_attachment(self, folder_id):
        """
        Method an item to a different parent (Used only for stand alone attachments to move between models)

        Args:
         * folder_id - sync.model or sync.object object (although sync.object is not a case)

        Methods:
         * move_or_update_item_o of client
         * _check_token_expiration()

        Returns:
         * key, path or False, False if failed

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        self._check_token_expiration()
        try:
            client = self._context.get("client")
            drive = self._context.get("drive_id")
            result = client.move_or_update_item_o(
                drive_id=drive,
                drive_item_id=self.cloud_key,
                new_parent=folder_id.key,
                new_name=False,
            )
            res = result.get("id"), self.name
            self._context.get("s_logger").debug(
                u"The file {} ({}) is moved in OneDrive to the folder {}".format(self.name, self.id, folder_id.name)
            )
        except Exception as error:
            res = False, False
            self._context.get("s_logger").error(
                u"The file {} ({}) can't be moved in OneDrive. Reason: {}".format(self.name, self.id, error)
            )
        return res

    def _remove_attachment_from_cloud(self):
        """
        The method to remove linked file from a cloud storage
        1. "Item not found" error is fine, since nothing to unlink

        Methods:
         * delete_file_o of client
         * _check_token_expiration()

        Returns:
         * res - char of 3 possible values
           ** "not_synced" - it wasn't a sync attachment
           ** "success"
           ** "failure"

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        self._check_token_expiration()
        try:
            client = self._context.get("client")
            drive = self._context.get("drive_id")
            if self.cloud_key:
                client.delete_file_o(drive_id=drive, drive_item_id=self.cloud_key)
                res = "success"
                self._context.get("s_logger").debug(
                    u"The file {} ({}) is deleted from OneDrive".format(self.name, self.id)
                )
            else:
                res = "not_synced"
        except Exception as error:
            if type(error).__name__ == "NotFound":
                # 1
                res = "success"
                self._context.get("s_logger").warning(
                    u"The file {} ({}) is not deleted from OneDrive, since it hase been removed already".format(
                        self.name,
                        self.id,
                    )
                )
            else:
                res = "failure"
                self._context.get("s_logger").error(
                    u"The file {} ({}) can't be deleted from OneDrive. Reason: {}".format(self.name, self.id, error,)
                )
        return res

    @api.model
    def _return_tracked_changes(self):
        """
        The method to return tracked changes

        Methods:
         * _check_token_expiration()
         * _find_or_create_root_directory - to track changes only of the root directory
         * _get_tracked_changes of client

        Returns:
         * list of dicts, bool (whether we should not wait for more changes)
         * False, False --> if error
        """
        self._check_token_expiration()
        try:
            Config = self.env['ir.config_parameter'].sudo()
            deltaurl = Config.get_param('onedrive_delta_url', '') or False
            client = self._context.get("client")
            drive = self._context.get("drive_id")
            business_onedrive = safe_eval(Config.get_param('onedrive_business', 'False'))
            if business_onedrive:
                root_key = "root"
            else:
                root_key, root_path = self._find_or_create_root_directory()                
            res, deltaurl, full_changes = client._get_tracked_changes(drive_id=drive, parent=root_key, url=deltaurl)
            Config.set_param('onedrive_delta_url', deltaurl)                    
            self._context.get("s_logger").info(u"Set OneDrive Delta Url to {}".format(deltaurl))
        except Exception as error:
            res, deltaurl, full_changes = False, False, False
            self._context.get("s_logger").error(u"Tracked changes are not received. Reason: {}".format(error))
        return res, full_changes