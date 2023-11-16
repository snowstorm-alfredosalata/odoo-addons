# -*- coding: utf-8 -*-

import logging
import requests
from dateutil.relativedelta import relativedelta

from odoo import fields

_logger = logging.getLogger(__name__)

try:
    from microsoftgraph.client import Client
    from microsoftgraph import exceptions
    from microsoftgraph.decorators import token_required

    class OnedriveApiClient(Client):
        BASEONEDRIVEURL = "https://graph.microsoft.com/v1.0"

        def set_token(self, token):
            """Sets the Token for its use in this library.
            Args:
                token: A string with the Token.
            """
            if self.office365:
                self.office365_token = token
            else:
                self.token = token
                self.exprires_in = fields.Datetime.now() + relativedelta(seconds=3480)

        def _put_not_json(self, url, no_token=False, **kwargs):
            """
            The method to request put command to Microsoft Graph API
            """
            return self._request_not_json('PUT', url, no_token=no_token, **kwargs)

        def _request_not_json(self, method, url, headers=None, content_type="multipart/form-data", no_token=False,
                              **kwargs):
            """
            The method to request not in "application/json" format (Microsoft graph library doesn't support others)
            """
            _headers = {
                'Accept': 'application/json',
                'Content-Type': content_type,
            }
            if not kwargs.get("no_token"):
                # Sometimes, e.g. in case of multi upload sessions put, we should not pass token (it might lead to 401)
                _headers.update({'Authorization': 'Bearer ' + self.token['access_token'],})
            if headers:
                _headers.update(headers)
            return self._parse(requests.request(method, url, headers=_headers, **kwargs))

        def _get_content(self, url, **kwargs):
            """
            Re-write to parse 'content' of files
            """
            return self._request_content('GET', url, **kwargs)

        def _request_content(self, method, url, headers=None, **kwargs):
            """
            Re-write to parse 'content' of files
            """
            _headers = {
                'Accept': 'application/json',
                'Authorization': 'Bearer ' + self.token['access_token'],
            }
            if headers:
                _headers.update(headers)
            if 'files' not in kwargs:
                # If you use the 'files' keyword, the library will set the Content-Type to multipart/form-data
                # and will generate a boundary.
                _headers['Content-Type'] = 'application/json'
            return self._parse_content(requests.request(method, url, headers=_headers, **kwargs))

        def _parse_content(self, response, **kwargs):
            """
            Re-write to parse 'content' of files
            """
            self._parse(response=response) # to process errors
            try:
                res = response.content
            except:
                res = response.text
            return res

        @token_required
        def sharepoint_site_o(self, path, params=None):
            """
            Method to return sharepoint site

            Args:
             * path in a specified format. e.g. odootools.sharepoint.com:/sites/odootoolstest (without https:!)

            Returns:
             * dict
            """
            url = "{}/sites/{}/".format(self.BASEONEDRIVEURL, path)
            res = self._get(url, params=params)
            return res

        @token_required
        def drives_list_o(self, site_id, params=None):
            """
            The method to return all drives (document libraries) of sharepoint site

            Methods:
             * site_id - id of Sharepoint site

            Returns:
             * dict. Dict['value'] contains list of drives with ID
            """
            url = "{}/sites/{}/drives".format(self.BASEONEDRIVEURL, site_id)
            res = self._get(url, params=params)
            return res

        @token_required
        def personal_drive_o(self, params=None):
            """
            The method to return drive of personal / business account
            """
            url = "{}/me/drive".format(self.BASEONEDRIVEURL)
            res = self._get(url, params=params)
            return res

        @token_required
        def children_items_o(self, drive_id, drive_item_id, params=None):
            """
            The method to return children items of this drive
            API returns max 200 items + url for the next request. Thus, we should be in while loop

            Args:
             * drive_id - id of Drive
             * drive_item_id - id of DriveItem

            Returns:
             * list of dicts
            """
            url = "{}/drives/{}/items/{}/children?$top=100".format(self.BASEONEDRIVEURL, drive_id, drive_item_id)
            res = []
            while url:
              respo = self._get(url, params=params)
              res += respo.get("value")
              url = respo.get("@odata.nextLink") or False
            return res

        @token_required
        def get_drive_item_o(self, drive_id, drive_item_id, params=None):
            """
            The method to get OneDrive item by id

            Args:
             * drive_id - id of Drive
             * drive_item_id - id of DriveItem

            Returns:
             * dict
            """
            url = "{}/drives/{}/items/{}".format(self.BASEONEDRIVEURL, drive_id, drive_item_id)
            res = self._get(url, params=params)
            return res

        @token_required
        def create_folder_o(self, drive_id, folder_name, parent="root", params=None):
            """
            The method to create a new folder in Onedrive

            Args:
             * drive_id - Drive object id
             * folder_name - char - new folder name
             * parent - DriveItem object id or string - parent folder. If string, it should be always "root"
            """
            data = {
                "name": folder_name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename"
            }
            url = "{}/drives/{}/items/{}/children".format(self.BASEONEDRIVEURL, drive_id, parent)
            res = self._post(url, json=data, params=params)
            return res

        @token_required
        def move_or_update_item_o(self, drive_id, drive_item_id, new_parent=False, new_name=False, params=None):
            """
            The method to move a folder/file to a new parent (if parent is defined) or update a name (if new_name
            is defined)

            Args:
             * drive_id - Drive object id
             * drive_item_id - Drive item id
             * new_parent - DriveItem object id or string - new parent folder
             * new_name - char - new DriveItem name
            """
            data = {}
            if new_name:
                data.update({
                    "name": new_name,
                })
            if new_parent:
                data.update({
                    "parentReference": {
                        "id": new_parent,
                    },
                })
            res = False
            if data:
                url = "{}/drives/{}/items/{}".format(self.BASEONEDRIVEURL, drive_id, drive_item_id)
                res = self._patch(url, json=data, params=params)
            else:
                _logger.error("No parent id and no new name are defined")
            return res

        @token_required
        def upload_file_o(self, drive_id, folder_name, file_name, content, mimetype, params=None):
            """
            The method to upload a new file (<4mb).

            Args:
             * drive_id - Drive object id
             * folder_name - DriveItem object - parent folder
             * file_name - the name of uploaded file
             * content - binary
             * mimetype - request content type, e.g. image/jpg

            Extra info:
             *  This method doesn't support duplicated names check, USE upload_large_file_o
            """
            url = "{}/drives/{}/items/{}:/{}:/content".format(self.BASEONEDRIVEURL, drive_id, folder_name, file_name)
            res = self._put_not_json(url=url, content_type=mimetype, data=content, params=params)
            return res

        @token_required
        def upload_large_file_o(self, drive_id, folder_name, file_name, content, file_size, params=None):
            """
            The method to upload a new file (>= 4mb)

            Args:
             * drive_id - Drive object id
             * folder_name - DriveItem object - parent folder
             * file_name - the name of uploaded file
             * content - binary
             * file_size - integer

            Methods:
             * generate_upload_session_o
            """
            upload_session = self.generate_upload_session_o(drive_id=drive_id, folder_name=folder_name, file_name=file_name,
                                                            params=params).get("uploadUrl")
            headers = {
                "Content-Length": str(file_size),
                "Content-Range": "bytes 0-{}/{}".format(file_size-1, file_size)
            }
            res = False
            upload_file = self._put_not_json(url=upload_session, content_type="application/json", headers=headers,
                                             no_token=True, params=params, data=content)
            if upload_file.get("error"):
                self._delete(upload_session)
                _logger.error("File was not uploaded. Error: {}".format(upload_file))
            else:
                res = upload_file
            return res

        @token_required
        def generate_upload_session_o(self, drive_id, folder_name, file_name, params=None):
            """
            The method to prepare an Upload session for a large file

            Args:
             * drive_id - Drive object id
             * folder_name - DriveItem object - parent folder

            To-do:
             * in case file > 60 MiB, we should split files in a few sessions. It is not yet done, since Odoo attachments
               have resriction of 25 mb
            """
            data = {
                "item": {
                    "@microsoft.graph.conflictBehavior": "rename",
                }
            }
            url = "{}/drives/{}/items/{}:/{}:/createUploadSession".format(self.BASEONEDRIVEURL, drive_id,
                                                                          folder_name, file_name)
            res = self._post(url, json=data, params=params)
            return res

        @token_required
        def download_file_o(self, drive_id, drive_item, params=None):
            """
            The method to download a file from Onedrive

            Args:
             * drive_id - id of Drive
             * drive_item - id of DriveItem

            Returns:
             * dict
            """
            url = "{}/drives/{}/items/{}/content".format(self.BASEONEDRIVEURL, drive_id, drive_item)
            res = self._get_content(url=url)
            return res

        @token_required
        def delete_file_o(self, drive_id, drive_item_id, params=None):
            """
            The method to upload a new file (<4mb).

            Args:
             * drive_id - Drive object id
             * drive_item_id - DriveItem to delete
            """
            url = "{}/drives/{}/items/{}".format(self.BASEONEDRIVEURL, drive_id, drive_item_id)
            res = self._delete(url, params=params)
            return res

        @token_required
        def _get_tracked_changes(self, drive_id, parent, url=False, params=None):
            """
            The method to get changes

            Args:
             * drive_id - Drive object id
             * parent - DriveItem object id or string (if string - always "root")
             * url - Changes since the last request

            Returns:
             * list of dicts - changes
             * deltaurl - the state of changes
             * full_changes - bool - whether we should apply changes or wait for the whole loop 

            Extra info:
             * We do not use token=latest any more since now we work with 'Odoo' folder only, and historical changes
               do not exist 
             * We are in try since in case of huge loop we should get at least nextLink if we do not have delta
               In such a case tracked changes should not be applied, since we should have all changes at all
            """
            delta_url = url or ""
            if not url:
                if parent == "root":
                    url = "{}/drives/{}/root/delta?$top=100".format(self.BASEONEDRIVEURL, drive_id, parent)
                else:
                    url = "{}/drives/{}/items/{}/delta?$top=100".format(self.BASEONEDRIVEURL, drive_id, parent)
            res = []
            full_changes = True
            while url:
                try:
                    respo = self._get(url, params=params)
                    res += respo.get("value")
                    url = respo.get("@odata.nextLink") or False
                    delta_url = respo.get("@odata.deltaLink") or url
                except Exception as error:
                    _logger.error('Delta url is not received by {}: {}'.format(url, error))
                    url = full_changes = False
            return res, delta_url, full_changes

        def _parse(self, response):
            """
            Re-write to log error status code
            """
            if response.status_code not in (200, 201, 202):
                try:
                    _logger.error('OneDrive Status Code Error: {}, {}'.format(response.status_code, response.reason))
                except:
                    pass
            return super(OnedriveApiClient, self)._parse(response)

except Exception as error:
    _logger.error('Cannot import microsoftgraph: {}'.format(error))
