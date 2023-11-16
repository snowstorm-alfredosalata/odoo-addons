# -*- coding: utf-8 -*-

import json
import logging
from datetime import timedelta

from odoo import _, api, fields, models, registry
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)

FORBIDDENSYMBOLS = ['~', '#', '&', ':', '{', '}', '*', '?', '"', "'", '<', '>', '|', '+', '%', '!', '@', '\\', '/']
SPECIAL_MIMETYPES = [
    "application/vnd.google-apps.spreadsheet", "application/vnd.google-apps.document",
    "application/vnd.google-apps.presentation",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
]
FOLDER_MIMETYPES = ["application/vnd.google-apps.folder", "dir"]


def check_allowed_mimetypes(mimetype):
    """
    This mimetype is required only for 'special' mimetypes. Standard ones are defined by Odoo
    """
    available_mimetypes = SPECIAL_MIMETYPES + FOLDER_MIMETYPES
    if not mimetype or mimetype not in (SPECIAL_MIMETYPES + FOLDER_MIMETYPES):
        mimetype = False
    elif mimetype in FOLDER_MIMETYPES:
        mimetype = "special_cloud_folder"
    return mimetype

class ir_attachment(models.Model):
    """
    Overwritting to prepare method for cloud api methods

    When use:
     * Introduce to-implement methods (in the bottom)
     * Try to optimize cron_synchronize_attachments_backward if sth like 'track changes' method exists in a client
    """
    _inherit = "ir.attachment"

    @api.depends('store_fname', 'db_datas')
    def _compute_datas(self):
        """
        Fully re-write core function to pass cloud_key to file-read
        """
        bin_size = self._context.get('bin_size')
        for attach in self:
            if attach.store_fname:
                attach.datas = self._file_read(attach.store_fname, bin_size)
            elif attach.type == "url" and attach.cloud_key:
                try:
                    attach.datas = self._file_read(attach.store_fname, bin_size, attach)
                except:
                    attach.datas = False
            else:
                attach.datas = attach.db_datas

    def _inverse_datas(self):
        """
        Overwrite to avoid writing on cloud datas into Odoo
        """
        for attach in self:
            if not attach.cloud_key:
                super(ir_attachment, attach)._inverse_datas()

    last_sync_datetime = fields.Datetime(string="Time of last update")
    for_delete = fields.Boolean(default=False, string="Marked for delete")
    active = fields.Boolean(default=True, string="Active")
    cloud_key = fields.Char(string="Cloud key", copy=False)
    cloud_path = fields.Char(string="Cloud path", copy=False)
    sync_model_id = fields.Many2one(
        "sync.model",
        string="Synced Model",
        copy=False,
        help="Only for stand-alone attachments",
    )

    def read(self, fields=None, load='_classic_read'):
        """
        Overwrite to allow reading records marked to delete by using the "show_for_delete"
        context keyword
        """
        if fields and 'for_delete' not in fields:
            fields = fields + ['for_delete']
        if fields and "cloud_key" not in fields:
            # to have in widgets
            fields = fields + ['cloud_key']
        result = super(ir_attachment, self).read(fields=fields, load=load)
        if self._context.get('show_for_delete', False):
            result = [a for a in result if not a.get('for_delete')]
        return result

    def unlink(self):
        """
        Overwite since unlink now is 2-step-process:
         1. Firstly deactivate attachments (mark them for 'delete')
         2. Only then unlink (usually during a sync)

        Extra info:
         * We do not remove binary attachments here for sudden cases when sync and unlink are simultaneous
        """
        self.check('unlink')
        for_delete = self.filtered(lambda a: a.for_delete)
        mark_for_delete = self - for_delete
        values = {
            'for_delete': True,
            'active': False,
        }
        mark_for_delete.write(values)
        result = super(ir_attachment, for_delete).unlink()
        return result

    def copy(self, default=None):
        """
        Overwrite not allow to copy attachments marked to delete
        """
        self.check('write')
        if self.for_delete:
            raise UserError("Can't copy attachments marked to delete.")
        return super(ir_attachment, self).copy(default)

    @api.model
    def _file_read(self, fname, bin_size=False, attach_cloud_id=False):
        """
        Rewrite to read files from Cloud client

        Extra Args:
         * attach_cloud_id - ir.attachment object

        Extra Methods:
         * _return_client_context
         * _upload_attachment_from_cloud

        Extra info:
         * We init client here to avoid initiating each time ANY attachment is read
        """
        if not attach_cloud_id:
            r = super(ir_attachment, self)._file_read(fname=fname, bin_size=bin_size)
        else:
            ctx = self._context.copy()
            if "client" not in ctx.keys():
                new_ctx = self.sudo()._return_client_context()
                ctx.update(new_ctx)
            attach = attach_cloud_id.with_context(ctx)
            r = attach.sudo()._upload_attachment_from_cloud()
            if not r:
                raise UserError(_(u"Datas can't be retrieved from clouds".format()))
        return r

    def upload_attachment_from_cloud_ui(self):
        """
        The method to be executed in UI to download binary

        Returns:
         * dict - url action

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        url = "/web/cloud_content/{}".format(self.id,) 
        return {
            "type": "ir.actions.act_url",
            "url": url,
            'target': 'new',
        }

    def _normalize_name(self):
        """
        Inverse method to make name legalized

        Methods:
         * remove_illegal_characters of ir.attachment

        Extra info:
         * Expected Singleton
        """
        self.ensure_one()
        attach = self
        legal_name = self.remove_illegal_characters(attach.name)
        if not legal_name:
            legal_name = str(attach.id)
        return legal_name

    @api.model
    def remove_illegal_characters(self, s):
        """
        The method to replace not allowed in Onedrive characters
        It is not global to use in all Clients

        Args:
         * s - string

        Returns:
         * s - string (might be empty!)
        """
        for symbol in FORBIDDENSYMBOLS:
            s = s.replace(symbol, "-")

        def find_index_dot(s_list):
            start = 0
            for symbol in s_list:
                if symbol == ".":
                    start += 1
                else:
                    break 
            return start    

        start = find_index_dot(s)
        end = find_index_dot(reversed(s))
        if start:
            s = s[start:]
        if end:
            s = s[:-end]      
        s = s.strip(" ")
        return s

    def _filter_document_attachments(self):
        """
        The method to return only attachments for ordinary (not documents) sync

        This method is overwritten in the extension for 'Document compatibility'
        """
        return self

    def _filter_non_synced_attachments(self):
        """
        The method to filter system attachments

        Retunrs:
         * ir.attachment recordset
        """
        mime_types = json.loads(self.env['ir.config_parameter'].sudo().get_param('not_sync_mime_types', '{}'))
        attachments = self
        for attachment in self:
            not_sync = (
                attachment.mimetype in mime_types.values()
                or attachment.name.startswith('/')
                or (attachment.url and attachment.url.startswith('/'))
                or attachment.res_field
                or attachment.file_size <= 0
            )
            if not_sync:
                attachments -= attachment
        return attachments

    @api.model
    def _make_cloud_files(self, folder_id, res_model, res_id, attachments=None, sync_model_id=False):
        """
        The method to filter and upload attachments to cloud
        We consider only binary attachments here, since attachments unlink happens separately

        Args:
         * folder_id - sync.object or sync.model object
         * res_model - model_name
         * res_id - id of related object
         * attachments - it.attachment recordset - for stand alone attachments
         * sync_model_id - sync.model object - for stand alone attachments

        Methods:
         * _filter_non_synced_attachments
         * _filter_document_attachments
         * _send_attachment_to_cloud
         * _update_attachment_as_cloud
        """
        if fields.Datetime.now() >= self._context.get("cloud_timeout"):
            return
        attachment_ids = attachments
        if attachment_ids is None:
            query = """SELECT id FROM ir_attachment
                       WHERE res_model = %s AND res_id = %s AND type = %s
                       ORDER BY last_sync_datetime ASC"""
            self._cr.execute(query, (res_model, res_id, "binary"))
            attach_ids = self._cr.fetchall()
            attachment_ids = self.browse([at[0] for at in attach_ids])
            attachment_ids = attachment_ids._filter_document_attachments()
        attachments_for_sync = attachment_ids._filter_non_synced_attachments()
        for record in attachments_for_sync:
            today_now = fields.Datetime.now()
            res = record._send_attachment_to_cloud(folder_id=folder_id)
            if res:
                record._update_attachment_as_cloud(res, today_now, sync_model_id)

    def _update_attachment_as_cloud(self, res, today_now, sync_model_id):
        """
        The method to introduce changes to attachment based on cloud taken info
        
        Args:
         * res - dict of cloud values
         * today_now - datetime.datetime
         * sync_model_id - sync.model object or False
        
        Methods:
         * _file_delete
        
        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        res_id = res.get("res_id")
        url = res.get("url")
        name = res.get("filename")
        path = res.get("path")
        store_fname = self.store_fname
        self._file_delete(store_fname)
        query = """UPDATE ir_attachment
                   SET cloud_key = %s,
                       cloud_path = %s,
                       url = %s,
                       store_fname = NULL,
                       type = 'url',
                       last_sync_datetime = %s,
                       name = %s,
                       sync_model_id = %s
                   WHERE id = %s
                """
        self._cr.execute(query, (
            res_id, path, url, today_now, name, sync_model_id and sync_model_id.id or None, self.id,
        ))
        self._cr.commit()

    def _reconcile_stand_alone_attachments(self, sync_model_id):
        """
        The method to change stand-alone attachment parent folder

        Args:
         * sync_model_id - sync.object or sync.model object

        Methods:
         * _move_attachment
         * write

        Extra info:
         * We do not filter for non-synced, since we pass here once which have already key and ARE synced
        """
        today_now = fields.Datetime.now()
        for record in self:
            key, path = record._move_attachment(folder_id=sync_model_id)
            if key and path:
                record.write({
                    "cloud_path": path, # key should not be updated
                    "sync_model_id": sync_model_id.id,
                    "last_sync_datetime": today_now,
                })
                self._cr.commit()

    @api.model
    def _update_folders(self):
        """
        The method to update folders

        1. Create root directory
        2. Prepare models' structure
         2.1. Logic f ir.atachment models is different. It doesn't have object folders
        3. Firstly we get all synced folders and check their existance in client
           We can't check that in the loop further, since a folder might relate to another model already.
        4. Prepare records' structure
           The order of to to_sync_models should remain the same. Since one record migth relate to a few models and
           we take the first
           We rely on the principle: a single folder for one object (model of object is not changeable)
          4.1. We go from the most prioritized folder to a least one. Thus, if records have been already synced, no
               sense to sync them another time within a least prioritized model folder
          4.2. To understand whether we need update of a folder we compare it to actual CLOUD name
        5. Check attachments for sync. If folder_id exist, it is guaranteed parent model exists. Thus, attachments
           might be safely upload
        6. Sync stand alone attachments
         6.0. To avoid relocation attachments to the least prioritized model folder
         6.1. Reconcile current attachments: there might be a few ir.attachment folders - we should move
         6.2. Upload new binary files

        Methods:
         * _find_or_create_root_directory: create 'Odoo'
         * _return_sync_domain of sync.model
         * _return_children_batch of sync.model
         * _find_object_folder of sync.object
         * _reconcile_object_folder of sync.object
         * _create_and_send
         * _reconcile_stand_alone_attachments
         * _filter_document_attachments
         * _make_cloud_files

        Returns:
         * bool: True if eth is fine; False - if timed out
        """
        Config = self.env['ir.config_parameter'].sudo()
        to_sync_model_ids = safe_eval(Config.get_param("odoo_models_to_sync", "[]"))
        sync_model_obj = self.env["sync.model"]
        sync_object_object = self.env["sync.object"]
        cloud_timeout = self._context.get("cloud_timeout")
        # 1
        root_key, root_path = self._find_or_create_root_directory()
        if not root_key or not root_path:
            return None
        self._cr.commit()
        # 2
        to_sync_models = self.sudo().env["sync.model"].search(
            [("id", "in", to_sync_model_ids)],
            order="nosyncd ASC, last_sync_datetime, id",
        )
        sync_model_res = to_sync_models._make_cloud_models(root_key=root_key, root_path=root_path)
        if not sync_model_res:
            return None
        # 2.1
        stand_alone_attachments = to_sync_models.filtered(lambda mod: mod.model == "ir.attachment")
        to_sync_models -= stand_alone_attachments
        # 3
        client_items = to_sync_models._return_children_batch()
        if client_items is None:
            return None
        client_items_set = {i['id'] for i in client_items}
        synced_folders = sync_object_object.search([("key", "!=", False)])
        odoo_items = synced_folders.mapped("key")
        odoo_items_set = set(odoo_items)
        to_recover_objects_set = odoo_items_set - client_items_set
        to_recover_objects = synced_folders.filtered(lambda fol: fol.key in to_recover_objects_set)
        to_recover_objects.write({"key": False})
        # 4
        already_synced_records = {} # "model_name": [ids]
        for sync_model in to_sync_models:
            model_name = sync_model.model
            domain = sync_model._return_sync_domain()
            synced_already = already_synced_records.get("model_name")
            if synced_already:
                # 4.1
                domain += [("id", "not in", synced_already)]
            if hasattr(self.env[model_name], 'active'):
                domain += [
                    '|',
                        ('active', '=', True),
                        ('active', '=', False)
                ]
            record_ids = self.env[model_name].search(domain)
            already_synced_records.update({
                model_name: synced_already and synced_already + record_ids.ids or record_ids.ids,
            })
            for record in record_ids:
                if fields.Datetime.now() >= cloud_timeout:
                    return False

                folder_id = sync_object_object._find_object_folder(res_model=model_name, res_id=record.id)
                if folder_id:
                    if folder_id.key:
                        # 4.2
                        client_datax = [
                            [item["name"], item["path"]] for item in client_items if item["id"] == folder_id.key
                        ]
                        if client_datax:
                            client_data = client_datax[0]
                            cfolder_name, cfolder_path = client_data[0], client_data[1]
                            folder_id._reconcile_object_folder(
                                sync_model_id=sync_model,
                                client_name=cfolder_name,
                                client_path=cfolder_path,
                            )
                    else:
                        # to recover broken client folder
                        folder_id._write_and_send(sync_model_id=sync_model)
                else:
                    folder_id = sync_object_object._create_and_send(
                        sync_model_id=sync_model,
                        res_model=sync_model.model,
                        res_id=record.id,
                    )
                # 5
                if folder_id:
                    self._make_cloud_files(
                        folder_id=folder_id,
                        res_model=model_name,
                        res_id=record.id,
                    )
        # 6
        already_synced_records = []
        for sync_model in stand_alone_attachments:
            if fields.Datetime.now() >= cloud_timeout:
                return False

            domain = sync_model._return_sync_domain()
            domain += [
                ("id", "not in", already_synced_records), # 6.0
                "|",
                    ("res_id", "=", False),
                    ("res_id", "=", 0),
                "|",
                    ("active", "=", True),
                    ("active", "=", False),
            ]
            # 6.1
            to_reconcile_domain = domain + [
                ("type", "=", "url"),
                ("cloud_key", "!=", False),
                ("sync_model_id", "!=", sync_model.id), # only attachments with changed parent
            ]
            to_reconcile_attachments = self.search(to_reconcile_domain, order="last_sync_datetime ASC")
            to_reconcile_attachments = to_reconcile_attachments._filter_document_attachments()
            to_reconcile_attachments._reconcile_stand_alone_attachments(sync_model_id=sync_model)

            # 6.2
            to_upload_domain = domain + [("type", "=", "binary"),]
            attachments = self.search(to_upload_domain, order="last_sync_datetime ASC")
            attachments = attachments._filter_document_attachments()
            if attachments:
                self._make_cloud_files(
                    folder_id=sync_model,
                    res_model=False,
                    res_id=False,
                    attachments=attachments,
                    sync_model_id=sync_model,
                )
            already_synced_records += to_reconcile_attachments.ids + attachments.ids
        return True

    @api.model
    def _remove_marked_to_delete_attachments(self):
        """
        The method to unlink marked to delete attachments
         1. Binary attachments are just removed
         2. For url attachments: only in case
            (a) file is successfully removed in Client
            (b) or it was never in client
            We unlink it here. Otherwise, it would still exist (mainly in case API fails)
            The most of failed attachments should be unlinked in backward sync (it is the situation when atttachment
            is removed from Odoo and from client before a real sync)

        Methods:
         * _remove_attachment_from_cloud

        Extra info:
         * We remove binary attachments here not in unlink for sudden cases when sync is done simultaneously
        """
        binary_attachments = self.with_context(show_for_delete=True).env['ir.attachment'].search(
            [
                ('for_delete', '=', True),
                ('type', '!=', 'url'),
                '|',
                    ('active', '=', True),
                    ('active', '=', False)
            ],
        )
        binary_attachments.unlink()
        self._cr.commit()       
        url_attachments = self.with_context(show_for_delete=True).env['ir.attachment'].search(
            [
                ('for_delete', '=', True),
                ('type', '=', 'url'),
                '|',
                    ('active', '=', True),
                    ('active', '=', False)
            ],
            order='last_sync_datetime ASC',
        )
        for record in url_attachments:
            res = record._remove_attachment_from_cloud()
            if res in ["not_synced", "success"]:
                record.unlink()
            self._cr.commit()

    @api.model
    def _remove_object_folders(self):
        """
        The method to find sync.object which related records have been unlinked and delete Client folders

        Methods:
         * _check_object_exist
         * _delete_object_folder
        """
        folder_ids = self.env["sync.object"].search([])
        folder_to_unlink = folder_ids.filtered(lambda folder: not folder._check_object_exist())
        folder_to_unlink._delete_object_folder()

    @api.model
    def _find_folder_by_key(self, parent_key):
        """
        The method to find sync.object or sync.model by key to define attachment folder
         1. Try to find among sync.object
         2. If not found try to get sync.model object
            We filter by ir.attachment, since other model folders do not suit

        Args:
         * parent_key - key of searched folder

        Returns:
         * folder_obj - either sync.object, sync.model or False
         * res_model - model name
         * res_id - number of related record
         * sync_model_id - id of related sync.model
        """
        folder_obj = res_model = res_id = sync_model_id = False
        # 1
        if parent_key:
            query = 'SELECT id FROM sync_object WHERE key = %s'
            self._cr.execute(query, (parent_key,))
            folder_ids = self._cr.fetchall()
            if folder_ids:
                folder_obj = self.env["sync.object"].browse(folder_ids[0][0])
                res_model = folder_obj.sync_model_id.model
                res_id = folder_obj.res_id
            else:
                # 2
                query = 'SELECT id FROM sync_model WHERE key = %s and model = %s'
                self._cr.execute(query, (parent_key, 'ir.attachment',))
                model_ids = self._cr.fetchall()
                if model_ids:
                    folder_obj = self.env["sync.model"].browse(model_ids[0][0])
                    sync_model_id = model_ids[0][0]
        return folder_obj, res_model, res_id, sync_model_id

    def open_cloud_link(self):
        """
        The method to get action for opening cloud link
        """
        self = self.sudo()
        res = False
        if self.url:
            res = {
                'name': _('Open Cloud Item'),
                'res_model': 'ir.actions.act_url',
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': self.url,
            }
        return res        

    @api.model
    def open_cloud_folder(self, args):
        """
        The method to get url of this object folder and open it in Clouds
        Used mainly for js
         1. This is needed when we try to:
          * find a folder for stand-alone attachments
          * open attachment folder from attachment form

        Args:
         * args - dict of values
          ** res_model - char
          ** res_id - char

        Methods:
         * _return_client_context
         * _get_folder

        Returns:
         * action to open url
         * False if url can't be retrieved
        """
        self = self.sudo()
        ctx = self._context.copy()
        new_ctx = self._return_client_context()
        ctx.update(new_ctx)
        self = self.with_context(ctx)
        res_model = args.get("res_model")
        res_id = args.get("res_id")
        folder_obj = False
        # 1
        if res_model == "ir.attachment":
            attach_id = self.browse(res_id)
            if not attach_id.res_model or not attach_id.res_id:
                folder_obj = attach_id.sync_model_id
            else:
               folder_obj = self.env["sync.object"]._find_object_folder(
                   res_model=attach_id.res_model,
                   res_id=attach_id.res_id,
               )
        else:
            folder_obj = self.env["sync.object"]._find_object_folder(res_model=res_model, res_id=res_id)
        res = False
        if folder_obj:
            result = self._get_folder(folder_id=folder_obj)
            if result and result.get("url"):
                res = {
                    'name': _('Open Cloud Folder'),
                    'res_model': 'ir.actions.act_url',
                    'type': 'ir.actions.act_url',
                    'target': 'new',
                    'url': result.get("url")
                }
        return res

    @api.model
    def _sync_documents_folders(self):
        """
        In case 'Documents' is installed, need to sync its folders and files
        Managed in the stand-alone module
        """
        return True

    @api.model
    def _backward_sync_documents_folders(self):
        """
        In case 'Documents' is installed, need to sync cloud files for that folders as well
        Managed in the stand-alone module
        """
        return True

    ####################################################################################################################
    ##################################   CRON METHODS   ################################################################
    ####################################################################################################################
    @api.model
    def cron_synchronize_attachments(self):
        """
        Method for synchronization with a cloud storage

        Methods:
         * _return_client_context - to init client
         * _update_folders - to make general upload
         * _remove_marked_to_delete_attachments - to remove system attachments
         * _remove_object_folders - to remove folders of unlinked records
         * _sync_documents_folders

        Extra info:
         * We check order of synces with the goal to make sure that normal and enterprise sync works correctly
         * We make deletion of attachments separately from sync, since ordinary not synced attachments are also deleted
         * We remove objects finally since: (a) new folders should be firstly created; (b) it is not important
        """
        Config = self.env['ir.config_parameter'].sudo()
        if Config.get_param("cloud_client_state", "draft") == "confirmed":
            self = self.sudo()
            cloud_interval = int(Config.get_param("cloud_timeout", "900"))
            cloud_interval = (cloud_interval >= 900 and cloud_interval or 900) - 120
            cloud_timeout = fields.Datetime.now() + timedelta(0,cloud_interval)
            ctx = self._context.copy()
            new_ctx = self._return_client_context()
            ctx.update(new_ctx)
            ctx.update({"cloud_timeout": cloud_timeout})
            self = self.with_context(ctx)
            order = Config.get_param('sync_sync_order', '1')
            if order == "1":
                Config.set_param('sync_sync_order', "2")
                folder_res = self._sync_documents_folders()
                if not folder_res:
                    return
                cont_res = self._update_folders()
                if not cont_res:
                    return
                self._remove_marked_to_delete_attachments()
            elif order == "2":
                Config.set_param('sync_sync_order', "3")
                cont_res = self._update_folders()        
                if not cont_res:
                    return
                folder_res =  self._sync_documents_folders()
                if not folder_res:
                    return
                self._remove_marked_to_delete_attachments()
            elif order == "3":
                Config.set_param('sync_sync_order', "4") 
                self._remove_marked_to_delete_attachments()
                folder_res =  self._sync_documents_folders()
                if not folder_res:
                    return
                cont_res = self._update_folders()
                if not cont_res:
                    return
            else:
                Config.set_param('sync_sync_order', "1") 
                self._remove_marked_to_delete_attachments()
                cont_res = self._update_folders()  
                if not cont_res:
                    return
                folder_res = self._sync_documents_folders()
                if not folder_res:
                    return
            self._remove_object_folders()
        else:
            try:
                self._remove_marked_to_delete_attachments()
            except:
                _logger.warning("Attachments cannot be removed")


    @api.model
    def cron_synchronize_attachments_backward(self):
        """
        Cron for updatig files from Client
         1. We are in new environment not to make concurrent updates. Instead of self use new_env["ir.attachment"]
         2. We search new / removed files only within related object folders and stand-alone attachment folders
          2.0 Stand-alone attachments is not a folder, but a model
          2.1 That sorting is needed to make sure firstly oldest folders are synced
          2.2 >99 percent of time relates to this operation (except update of attachments)
         3. Create missing Odoo attachments
          3.1 We purposefully make this search instead of get from client to avoid too frequent requests
         4. Unlink attachments which files were removed from client
           4.1. To avoid filtering deleted items while trying to update names. Otherwise, 'Record does not exist or
                has been deleted.'
         5. Update name of attachments (IMPORTANT: goes through all attachments!).

        Methods:
         * _return_client_context
         * _backward_sync_documents_folders
         * _return_children of sync.object
         * _filter_document_attachments
         * create
         * unlink
         * write
         * remove_illegal_characters

        Extra info:
         * new folders also pursposefully generate attachments in Odoo (not their content)
         * we do not get all children items and then check, since if failed job would not be able to sync even part
           (we would need firstyly to proceed get_children which equal the number of records)
        """
        Config = self.env['ir.config_parameter'].sudo()
        if Config.get_param("cloud_client_state", "draft") != "confirmed":
            return True
        self = self.sudo()
        ctx = self._context.copy()
        new_ctx = self._return_client_context()
        ctx.update(new_ctx)
        cloud_interval = int(Config.get_param("cloud_timeout", "0"))
        cloud_interval = (cloud_interval >= 900 and cloud_interval or 900) - 120
        cloud_timeout = fields.Datetime.now() + timedelta(0,cloud_interval)
        ctx.update({"cloud_timeout": cloud_timeout})
        # 1
        with api.Environment.manage():
            with registry(self._cr.dbname).cursor() as new_cr:
                new_env = api.Environment(new_cr, self._uid, ctx)
                # 1
                long_ago = fields.Datetime.from_string("2018-01-01 00:00:00")
                attach_obj = new_env["ir.attachment"]
                order = Config.get_param('sync_sync_backward_order', '1')
                if order == "1":
                    Config.set_param('sync_sync_backward_order', '2')
                    con_res = attach_obj._backward_sync_documents_folders()            
                    if not con_res:
                        return
                else:
                    Config.set_param('sync_sync_backward_order', '1')
                sync_obj_obj = new_env["sync.object"]
                sync_mod_obj = new_env["sync.model"]
                object_ids = sync_obj_obj.search([("key", "!=", False)])
                folders = object_ids.mapped(lambda fol: {
                    "folder_obj": fol,
                    "res_model": fol.sync_model_id.model,
                    "res_id": fol.res_id,
                    "sync_model_id": False,
                    "sync_time": fol.last_backward_sync_datetime
                                 and fields.Datetime.from_string(fol.last_backward_sync_datetime)
                                 or long_ago,
                })
                # stand-alone attachments
                model_ids = sync_mod_obj.search([("model", "=", "ir.attachment"), ("key", "!=", False)])
                folders += model_ids.mapped(lambda mod: {
                    "folder_obj": mod,
                    "res_model": False,
                    "res_id": False,
                    "sync_model_id": mod.id,
                    "sync_time": mod.last_backward_sync_datetime
                                 and fields.Datetime.from_string(mod.last_backward_sync_datetime)
                                 or long_ago,
                })
                #1.1
                folder_ids = sorted(folders, key=lambda k: k['sync_time'])
                for folder in folder_ids:
                    if fields.Datetime.now() >= cloud_timeout:
                        return
                    folder_obj = folder.get("folder_obj")
                    res_model = folder.get("res_model")
                    res_id = folder.get("res_id")
                    sync_model_id = folder.get("sync_model_id")
                    # 2.2
                    client_items = folder_obj._return_children()
                    if client_items is not None:
                        client_items_set = {i['id'] for i in client_items}
                        odoo_items = new_env['ir.attachment'].search([
                            ('cloud_key', '!=', False),
                            ('res_model', '=', res_model),
                            ('res_id', '=', res_id),
                            ('sync_model_id', '=', sync_model_id),
                            '|',
                                ('active', '=', True),
                                ('active', '=', False),
                        ])
                        odoo_items_to_sync = odoo_items._filter_document_attachments()
                        odoo_items_set = set(odoo_items_to_sync.mapped("cloud_key"))
                        not_synced_items = odoo_items - odoo_items_to_sync
                        odoo_items_not_synce_set = set(not_synced_items.mapped("cloud_key"))

                        to_delete = odoo_items_set - client_items_set - odoo_items_not_synce_set
                        to_create = client_items_set - odoo_items_set - odoo_items_not_synce_set
                        to_update = client_items_set - to_create - odoo_items_not_synce_set

                        # 3
                        created = attach_obj
                        for oid in to_create:
                            # 3.1
                            if fields.Datetime.now() >= cloud_timeout:
                                return
                            oid_from_dict = [item for item in client_items if item["id"] == oid][0]
                            try:
                                values = {
                                    'name': oid_from_dict.get("name"),
                                    'res_model': res_model,
                                    'res_id': res_id,
                                    'type': 'url',
                                    'cloud_key': oid_from_dict.get("id"),
                                    'cloud_path': oid_from_dict.get("path"),
                                    'url': oid_from_dict.get("webUrl"),
                                    'sync_model_id': sync_model_id,
                                }
                                possible_mimetype = check_allowed_mimetypes(oid_from_dict.get("mimetype"))
                                if possible_mimetype:
                                    values.update({"mimetype": possible_mimetype})
                                created |= attach_obj.create(values)
                                attach_obj._context.get("s_logger").debug(
                                    u"Attachment {} is created from Cloud Client to {} ({})".format(
                                        oid_from_dict.get("name"),
                                        folder_obj.name,
                                        res_id and u"{},{}".format(res_model, res_id)
                                               or u"ir.attachment, {}".format(sync_model_id),
                                    )
                                )
                                new_cr.commit()
                            except Exception as error:
                                attach_obj._context.get("s_logger").error(
                                    u"Attachment {} can't be created from Cloud Client to {}. Reason: {}".format(
                                        oid_from_dict.get("name"), folder_obj.name, error
                                    )
                                )
                                new_cr.commit()
                        # 4
                        attachment_to_delete = odoo_items.filtered(lambda a: a.cloud_key in to_delete)
                        # 4.1
                        odoo_items -= attachment_to_delete
                        for attach in attachment_to_delete:
                            if fields.Datetime.now() >= cloud_timeout:
                                return
                            prev_attachment_name = attach.name
                            prev_attachment_id = attach.id
                            try:
                                attach.write({"for_delete": True}) # to delete attachment, not mark for delete
                                attach.unlink()
                                attach_obj._context.get("s_logger").debug(
                                    u"Attachment {} ({}) is deleted because it has been removed from Clouds".format(
                                        prev_attachment_name, prev_attachment_id
                                    )
                                )
                                new_cr.commit()
                            except Exception as error:
                                attach_obj._context.get("s_logger").error(
                                    u"Item {} can't be deleted from Odoo. Reason: {}".format(
                                        attach.id, error
                                    )
                                )
                                new_cr.commit()
                        # 5
                        attachment_to_update = odoo_items.filtered(lambda a: a.cloud_key in to_update)
                        for attach in attachment_to_update:
                            if fields.Datetime.now() >= cloud_timeout:
                                return
                            prev_attachment_name = attach.name
                            prev_attachment_id = attach.id
                            try:
                                res = [item for item in client_items if item["id"] == attach.cloud_key][0]
                                if prev_attachment_name != res.get("name") or attach.url != res.get("webUrl"):
                                    attach.write({
                                        "cloud_path": res.get("path"),
                                        "name": res.get("name"),
                                        "url": res.get("webUrl"),
                                        "last_sync_datetime": fields.Datetime.now(),
                                    })
                                    attach_obj._context.get("s_logger").debug(
                                        u"Attachment {} ({}) is updated from Cloud Client. New name is {}".format(
                                            prev_attachment_name, attach.id, res.get("name"),
                                        )
                                    )
                                    new_cr.commit()
                            except Exception as error:
                                attach_obj._context.get("s_logger").error(
                                    u"Attachment {} ({}) can't be updated from Cloud Client. Reason: {}".format(
                                        prev_attachment_name, prev_attachment_id, error,
                                    )
                                )
                                new_cr.commit()
                        folder_obj.write({"last_backward_sync_datetime": fields.Datetime.now()})
                        new_cr.commit()
                if order == "2":
                    con_res = attach_obj._backward_sync_documents_folders()  
                    if not con_res:
                        return

    ####################################################################################################################
    ##################################   TO IMPLEMENT CLIENT METHODS   #################################################
    ####################################################################################################################
    @api.model
    def _return_client_context(self):
        """
        The method to return necessary to client context (like session, root directory, etc.)
        Method to be overwritten in Client

        Returns:
         * dict
        """
        Config = self.env['ir.config_parameter'].sudo()
        sync_logs = safe_eval(Config.get_param('sync_logs', 'False'))
        if sync_logs:
            s_logger = self.env["sync.log"]
        else:
            s_logger = _logger
        with_context = {"s_logger": s_logger}
        return with_context

    @api.model
    def _find_or_create_root_directory(self):
        """
        Method to return root directory name and id
        Dummy method to be overwritten in Client

        Returns:
         * key, root_path - key and path in client
         * False if failed
        """
        raise NotImplementedError

    @api.model
    def _create_folder(self, folder_name, parent_folder_key, parent_folder_path):
        """
        Method to create folder in clouds
        Dummy method to be overwritten in Client

        Args:
         * folder_name - name of created folder
         * parent_folder_key - ID of parent folder in client
         * parent_folder_path - path of parent folder

        Returns:
         * key, path or False, False if failed

        Extra info:
         * here we can't use folder_id as sync.model / sync.object, since as a parent root my serves
        """
        raise NotImplementedError

    @api.model
    def _get_folder(self, folder_id):
        """
        Method to get folder in clouds
        Dummy method to be overwritten in Client

        Args:
         * folder_id - sync.model or sync.object
         * False if failed

        Returns:
         * dict of values including 'url'
        """
        raise NotImplementedError

    @api.model
    def _update_folder(self, folder_id, new_folder_name):
        """
        Method to update folder in clouds
        Dummy method to be overwritten in Client

        Args:
         * folder_id - sync.model or sync.object object (only such folders are updated)
         * new_folder_name - new name of folder

        Returns:
         * key, path or False, False if failed
        """
        raise NotImplementedError

    @api.model
    def _move_folder(self, folder_id, new_parent_key, new_parent_path):
        """
        Method to move folder in clouds to a different parent
        Dummy method to be overwritten in Client

        Args:
         * folder_id - sync.model or sync.object object (only such folders are moved, basically only sync.object)
         * new_parent_key - new parent folder key
         * new_parent_path - new parent folder path

        Returns:
         * key, path or False, False if failed
        """
        raise NotImplementedError

    @api.model
    def _remove_folder(self, folder_id):
        """
        Method to move folder in clouds to a different parent
        The method MUST check ItemNotFound, if so it is also success
        Dummy method to be overwritten in Client

        Args:
         * folder_id - sync.model or sync.object object (only such folders are removed)

        Returns:
         * True or False if failed
        """
        raise NotImplementedError

    @api.model
    def _return_child_items(self, folder_id, key=False, path=False):
        """
        Method to return child items of this folder
        The method MUST check ItemNotFound, if so it should pass empty list (to remove deleted attachments)
        Dummy method to be overwritten in Client

        Args:
         * folder_id - sync.model or sync.object object
         * key - key of a folder (used if no folder) - for the case of root
         * path -  path of a folder (used if no folder) - for the case of root

        Returns:
         * list of of child dicts including name, id, webUrl, path
         * None if error
        """
        raise NotImplementedError

    def _send_attachment_to_cloud(self, folder_id):
        """
        Method to send attachment to cloud
        It is a dummy method to be overwritten in a related client

        Args:
         * folder_id - sync.object or sync.model object - both might have attachments. The first - stand-alone ones

        Returns:
         * dict of res_id, url, filename, path
         * False if method failed

        Extra info:
         * Should be expected singleton
        """
        raise NotImplementedError

    def _upload_attachment_from_cloud(self):
        """
        Method to upload attachment from cloud

        Returns:
         * Binary File
         * False if method failed

        Extra info:
         * Use self.cloud_key or self.cloud_path
         * Should be expected singleton
        """
        raise NotImplementedError

    def _move_attachment(self, folder_id):
        """
        Method an item to a different parent (Used only for stand alone attachments to move between models)
        Dummy method to be overwritten in Client

        Args:
         * folder_id - sync.model or sync.object object (although sync.object is not a case)

        Returns:
         * key, path or False, False if failed

        Extra info:
         * Use self.cloud_key or self.cloud_path
         * Should be expected singleton
        """
        raise NotImplementedError

    def _remove_attachment_from_cloud(self):
        """
        The method to remove linked file from a cloud storage
        The method MUST check ItemNotFound, if so it is also success
        The method MUST rely upon ID. If path --> case of changed client name without backward sync is not considered
        It is a dummy method to be overwritten in a related client

        Returns:
         * res - char of 3 possible values
           ** "not_synced" - it wasn't a sync attachment
           ** "success"
           ** "failure"

        Extra info:
         * Use self.cloud_key or self.cloud_path
         * Should be expected singleton
        """
        return not_synced
