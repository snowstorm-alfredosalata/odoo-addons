# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class documents_folder(models.Model):
    """
    Overwrite to add sync options
    """
    _inherit = "documents.folder"

    @api.depends("last_sync_datetime")
    def _compute_nosyncd(self):
        """
        Compute method for nosyncd
        """
        for folder in self:
            nosyncd = False
            if folder.last_sync_datetime:
                nosyncd = True
            folder.nosyncd = nosyncd

    key = fields.Char(string="ID in client")
    path = fields.Char(string="Path")
    last_sync_datetime = fields.Datetime(string="Direct Sync Time")
    last_backward_sync_datetime = fields.Datetime(string="Backward Sync Time")
    nosyncd = fields.Boolean(
        string="Not synced",
        compute=_compute_nosyncd,
        store=True,
    )

    _sql_constraints = [
        (
            'name_parent_uniq',
            'unique(name, parent_folder_id)',
            _('The folder name should be unique within the same parent!'),
        )
    ]

    def _make_recursive_update(self, parent_key, parent_path):
        """
        Method to sync the folder recursively

        Args:
         * parent_key
         * parent_path

        Methods:
         * _reconcile_document_folder
         * _sync_folder_attachments
         * _make_recursive_update - to recursively update implied attachments

        Returns:
         * True if everything is fine
         * False if broken

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        if fields.Datetime.now() >= self._context.get("cloud_timeout"):
            return False
        parent_key, parent_path = self._reconcile_document_folder(parent_key=parent_key, parent_path=parent_path)
        self._sync_folder_attachments()
        for child_folder in self.children_folder_ids.sorted(lambda fol: (fol.nosyncd, fol.last_sync_datetime)):
            result = child_folder._make_recursive_update(parent_key=parent_key, parent_path=parent_path)
            if not result:
                return False
        return True

    def _reconcile_document_folder(self, parent_key, parent_path):
        """
        The method to create, update and delete folders

        1. Create folder if id doesn't yet exist
        2. If it exists, check that it is not moved or deleted
        3. If it exists, get it from another place and move back
        4. Check whether its name has been changed, and return an original name
        5. If a folder was removed, create a  new one

        Args:
         * parent_key - key of the parent folder
         * parent_path - path of the parent folder

        Methods:
         * remove_illegal_characters of ir.attachment
         * _check_item_exists_in_children of ir.attachment
         * _create_folder of ir.attachment
         * _get_folder of ir.attachment
         * _move_folder of ir.attachment
         * _update_folder of ir.attachment

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        ir_attachment = self.env["ir.attachment"]
        folder_name = ir_attachment.remove_illegal_characters(self.name)
        if not self.key:
            # 1
            key, path = ir_attachment._create_folder(
                folder_name=folder_name,
                parent_folder_key=parent_key,
                parent_folder_path=parent_path,
            )
        else:
            # 2
            key, path = ir_attachment._check_item_exists_in_children(
                parent_key=parent_key,
                parent_path=parent_path,
                checked_key=self.key,
                checked_path=self.path,
            )
            if not key:
                res = ir_attachment._get_folder(folder_id=self)
                if res:
                    # 3
                    key, path = ir_attachment._move_folder(
                        folder_id=self,
                        new_parent_key=parent_key,
                        new_parent_path=parent_path,
                    )
                    client_name = res.get("filename")
                    if folder_name != client_name:
                        # 4
                        key, path = ir_attachment._update_folder(
                            folder_id=self,
                            new_folder_name=folder_name,
                        )
                else:
                    key, path = ir_attachment._create_folder(
                        folder_name=folder_name,
                        parent_folder_key=parent_key,
                        parent_folder_path=parent_path,
                    )
        self.write({"key": key, "path": path,})
        self.env.cr.commit()
        return key, path

    def _sync_folder_attachments(self):
        """
        The method to sync this folders' attachments
         1.  Move a file to a proper folder in case
            (a) it was not in a folder previously (e.g. relates to an object)
            (b) it relates to a different folder
         2. Upload not yet synced attachments
         3. If a folder becomes absent, we try to find an ordinary folder to move.
            Stand-alone attachments reconcile files by themselves
            In case it is not possible to move a file (no proper folder found), we live it inside the original folder
            Deleting seems irrational since a file migth be still attached to some document
         4. URL or name migth be changed, we should fix that in documents as well   

        Methods:
         * _make_cloud_files
         * _move_attachment
         * _get_changes_from_attachments of document.document

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        ir_attachment = self.env["ir.attachment"]
        # 1
        to_move_attachment_ids = ir_attachment.search([
            ("type", "=", "url"),
            ("cloud_key", "!=", False),
            ("folder_id", "=", self.id),
            "|",
                ("previous_folder_id", "!=", self.id),
                ("previous_folder_id", "=", False),
            "|",
                ("active", "=", True),
                ("active", "=", False),
        ])
        for attach in to_move_attachment_ids:
            if fields.Datetime.now() >= self._context.get("cloud_timeout"):
                return
            attach._move_attachment(folder_id=self)
        # 2
        to_upload_attachment_ids = ir_attachment.search([
            ("type", "=", "binary"),
            ("folder_id", "=", self.id),
            "|",
                ("active", "=", True),
                ("active", "=", False),
        ])
        ir_attachment._make_cloud_files(
            folder_id=self,
            res_model=False,
            res_id=False,
            attachments=to_upload_attachment_ids,
            sync_model_id=False,
        )
        updated_attachments = to_move_attachment_ids + to_upload_attachment_ids
        updated_attachments.write({"previous_folder_id": self.id})
        #3
        excluded_attachment_ids = ir_attachment.search([
            ("type", "=", "url"),
            ("cloud_key", "!=", False),
            ("folder_id", "=", False),
            ("previous_folder_id", "=", self.id),
            "|",
                ("active", "=", True),
                ("active", "=", False),
        ])
        for attach in excluded_attachment_ids:
            if fields.Datetime.now() >= self._context.get("cloud_timeout"):
                return
            s_folder_id = self.env["sync.object"]._find_object_folder(res_model=attach.res_model, res_id=attach.res_id)
            if s_folder_id:
                attach._move_attachment(folder_id=s_folder_id)
        excluded_attachment_ids.write({"previous_folder_id": False})
        self.env.cr.commit()
        # 4
        to_move_attachment_ids.invalidate_cache()
        moved_documents = to_move_attachment_ids.mapped("document_ids")
        moved_documents._get_changes_from_attachments()
