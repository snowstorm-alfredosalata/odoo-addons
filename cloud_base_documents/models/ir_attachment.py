# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models

from odoo.addons.cloud_base.models.ir_attachment import check_allowed_mimetypes

_logger = logging.getLogger(__name__)


class ir_attachment(models.Model):
    """
    Overwritting to make sync of Odoo document folders and their attachments
    """
    _inherit = "ir.attachment"

    @api.depends("document_ids", "document_ids.folder_id")
    def _compute_folder_id(self):
        """
        Compute method for folder_id
        """
        for attachment in self:
            folder_id = False
            if attachment.document_ids:
                folder_id = attachment.document_ids[0].folder_id
            attachment.folder_id = folder_id

    folder_id = fields.Many2one(
        "documents.folder",
        compute=_compute_folder_id,
        compute_sudo=True,
        store=True,
    )
    document_ids = fields.One2many(
        "documents.document",
        "attachment_id",
        string="Related documents"
    )
    previous_folder_id = fields.Many2one(
        "documents.folder", 
        string="Previous Folder",
    )

    def _filter_document_attachments(self):
        """
        The method to return only attachments for ordinary (not documents) sync
        """
        res = super(ir_attachment, self)._filter_document_attachments()
        result = res.filtered(lambda attach: not attach.folder_id)
        return result

    @api.model
    def _sync_documents_folders(self):
        """
        The method to prepare documents folders structure in the client

        Methods:
         * _find_or_create_documents_dir_directory
         * _reconcile_document_folder
         * _sync_folder_attachments
        """
        res = super(ir_attachment, self)._sync_documents_folders()
        parent_key, parent_path = self._find_or_create_documents_dir_directory()
        parent_folder_ids = self.env["documents.folder"].search(
            [("parent_folder_id", "=", False)], 
            order="nosyncd ASC, last_sync_datetime, id",
        )
        for folder in parent_folder_ids:
            sync_res = folder._make_recursive_update(parent_key=parent_key, parent_path=parent_path)
            if not sync_res:
                return False
        return res

    @api.model
    def _find_or_create_documents_dir_directory(self):
        """
        The method to create 'Documents' directory within Odoo

        Methods:
         * _find_or_create_root_directory
         * _check_item_exists_in_children
         * _create_folder

        Returns:
         * key, path
        """
        root_key, root_path = self._find_or_create_root_directory()
        Config = self.env['ir.config_parameter'].sudo()
        documents_dir_key = Config.get_param('root_documents_dir_key', 'Odoo Docs')
        documents_dir_path = Config.get_param('root_documents_dir_path', 'Odoo Docs')
        key, path = self._check_item_exists_in_children(
            parent_key=root_key,
            parent_path=root_path,
            checked_key=documents_dir_key,
            checked_path=documents_dir_path,
        )
        if not key:
            key, path  = self._create_folder(
                folder_name="Odoo Docs", 
                parent_folder_key=root_key, 
                parent_folder_path=root_path
            )
        Config.set_param('root_documents_dir_key', key)
        Config.set_param('root_documents_dir_path', path)
        return key, path

    @api.model
    def _check_item_exists_in_children(self, parent_key, parent_path, checked_key, checked_path):
        """
        The method to reveal whether this item is present in target folder

        Args:
         * parent_key
         * parent_path
         * checked_key
         * checked_path

        Methods:
         * _return_child_items

        Returns:
         * key, path or False, False
        """
        client_items = self._return_child_items(folder_id=False, key=parent_key, path=parent_path)
        the_same_keys = [(item["id"], item["path"]) for item in client_items if checked_key == item["id"]]
        res = False, False
        if the_same_keys:
            res = the_same_keys[0][0], the_same_keys[0][1]
        else:
            the_same_pathes = [
                (item["id"], item["path"]) for item in client_items if checked_path == item["path"]
            ]
            if the_same_pathes:
                res = the_same_pathes[0][0], the_same_pathes[0][1]
        return res

    @api.model
    def _backward_sync_documents_folders(self):
        """
        The method to update attachments within Odoo documents folders
         0. We should launch direct sync here to avoid contradictions between
         1. The real Odoo folders should not be created, moved or updated as attachments

        Returns:
         * bool - True if everything fine; False - if timeouted

        Methods:
         * _return_child_items
        """
        res = super(ir_attachment, self)._backward_sync_documents_folders()
        # 0
        self._sync_documents_folders()
        attach_obj = self.env["ir.attachment"]
        folders = self.env["documents.folder"].search([("key", "!=", False)], order="last_backward_sync_datetime")
        for folder in folders:
            if fields.Datetime.now() >= self._context.get("cloud_timeout"):
                return False
            client_items = self._return_child_items(folder_id=folder)
            if client_items is not None:
                client_items_set = {i['id'] for i in client_items}
                odoo_items = attach_obj.search([
                    ('cloud_key', '!=', False),
                    ('folder_id', '=', folder.id),
                    '|',
                        ('active', '=', True),
                        ('active', '=', False),
                ])
                odoo_items_set = set(odoo_items.mapped("cloud_key"))
                # 1
                odoo_folders = self.env["documents.folder"].search([
                    ('key', '!=', False),
                    ('parent_folder_id', '=', folder.id),
                ])
                odoo_folders_set = set(odoo_folders.mapped("key"))

                to_delete = odoo_items_set - client_items_set  # NOT GOOD TO DELETE FILES NOT YET MOVED TO THE FOLDER!
                to_create = client_items_set - odoo_items_set - odoo_folders_set # 1
                to_update = client_items_set - to_create

                created = attach_obj
                for oid in to_create:
                    if fields.Datetime.now() >= self._context.get("cloud_timeout"):
                        return False
                    oid_from_dict = [item for item in client_items if item["id"] == oid][0]
                    try:
                        values = {
                            'name': oid_from_dict.get("name"),
                            'type': 'url',
                            'cloud_key': oid_from_dict.get("id"),
                            'cloud_path': oid_from_dict.get("path"),
                            'url': oid_from_dict.get("webUrl"),
                        }
                        possible_mimetype = check_allowed_mimetypes(oid_from_dict.get("mimetype"))
                        if possible_mimetype:
                            values.update({"mimetype": possible_mimetype})
                        new_attachment_id = attach_obj.create(values)
                        created |= new_attachment_id
                        document_vals = {
                            'attachment_id': new_attachment_id.id, 
                            'folder_id': folder.id,
                            'url': oid_from_dict.get("webUrl"),
                        }
                        self.env["documents.document"].create(document_vals)
                        attach_obj._context.get("s_logger").debug(
                            u"Attachment {} is created from Cloud Client to {}".format(
                                oid_from_dict.get("name"),
                                folder.name,
                            )
                        )
                        self.env.cr.commit()
                    except Exception as error:
                        attach_obj._context.get("s_logger").error(
                            u"Attachment {} can't be created from Cloud Client to {}. Reason: {}".format(
                                oid_from_dict.get("name"), folder.name, error
                            )
                        )
                        self.env.cr.commit()

                attachment_to_delete = odoo_items.filtered(lambda a: a.cloud_key in to_delete)
                odoo_items -= attachment_to_delete
                for attach in attachment_to_delete:
                    if fields.Datetime.now() >= self._context.get("cloud_timeout"):
                        return False
                    prev_attachment_name = attach.name
                    prev_attachment_id = attach.id
                    try:
                        attach.write({"for_delete": True}) # to delete attachment, not mark for delete
                        attach.document_ids.unlink()
                        attach_obj._context.get("s_logger").debug(
                            u"Attachment {} ({}) is deleted because it has been removed from Clouds".format(
                                prev_attachment_name, prev_attachment_id
                            )
                        )
                        self.env.cr.commit()
                    except Exception as error:
                        _logger.error(u"Item {} can't be deleted from Odoo. Reason: {}".format(
                            attach.id, error
                        ))
                        self.env.cr.commit()

                attachment_to_update = odoo_items.filtered(lambda a: a.cloud_key in to_update)
                for attach in attachment_to_update:
                    if fields.Datetime.now() >= self._context.get("cloud_timeout"):
                        return False
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
                            self.env.cr.commit()
                    except Exception as error:
                        attach_obj._context.get("s_logger").error(
                            u"Attachment {} ({}) can't be updated from Cloud Client. Reason: {}".format(
                                prev_attachment_name, prev_attachment_id, error,
                            )
                        )
                        self.env.cr.commit()
                folder.write({"last_backward_sync_datetime": fields.Datetime.now()})
                self.env.cr.commit()
        return res

    def _update_attachment_as_cloud(self, res, today_now, sync_model_id):
        """
        Re-write to add adaptation of documents
        """
        super(ir_attachment, self)._update_attachment_as_cloud(
            res=res, today_now=today_now, sync_model_id=sync_model_id
        )
        document = self.document_ids and self.document_ids[0] or False
        if document:
            self.invalidate_cache() # since attachments are sql updated
            vals = {
                "url": res.get("url"),
                "attachment_id": self.id, # to trigger related
            }
            document.write(vals)
            self._cr.commit()
