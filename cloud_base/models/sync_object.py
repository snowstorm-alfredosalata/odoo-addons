# -*- coding: utf-8 -*-

import json

from odoo import _, api, fields, models


class sync_object(models.Model):
    """
    The model to manage object - cloud folder relation
    """
    _name = "sync.object"
    _description = "List of Odoo synced objects"

    name = fields.Char(string="Folder name")
    sync_model_id = fields.Many2one(
        "sync.model",
        string="Model to sync",
    )
    res_id = fields.Integer("RES ID")
    key = fields.Char("ID in client")
    path = fields.Char(string="Path")
    last_sync_datetime = fields.Datetime(string="Direct Sync Time")
    last_backward_sync_datetime = fields.Datetime(string="Direct Backward Sync Time")

    def _check_object_exist(self):
        """
        The method to check whether res_model, res_id leads to a real record: needed to remove client folders

        Returns:
         * ID of related document if exists
         * False otherwise

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        try:
            res_model = self.env[self.sync_model_id.model]._table
            query = 'SELECT id FROM %s WHERE id = %s' % (res_model, self.res_id,)
            self._cr.execute(query)
            res = self._cr.fetchall()
        except:
            res = False
        return res

    @api.model
    def _return_folder_name(self, res_model, res_id, sync_model_id, current_id):
        """
        The method to make name safe:
         * without illegal charachers
         * unique

        Args:
         * res_model - model of related record
         * res_id - id of a related record
         * sync_model_id - sync.model object
         * current_id - id of this folder if exists

        Methods:
         * remove_illegal_characters of ir.attachment

        Returns:
         * proper name based on current conditions
        """
        record_id = self.env[res_model].browse(res_id)
        if sync_model_id.name_expression:
            try:
                name_formal = self.env["mail.template"]._render_template(
                    sync_model_id.name_expression,
                    res_model,
                    res_id,
                )
            except:
                name_formal = record_id.name_get()[0][1]
        else:
            name_formal = record_id.name_get()[0][1]
        name_formal = self.env["ir.attachment"].remove_illegal_characters(name_formal)
        legal_name = name_formal and name_formal or str(record_id.id)
        with_the_same_name = self.search([
            ("name", "=", legal_name),
            ("sync_model_id", "=", sync_model_id.id),
            ("id", "!=", current_id)]
        )
        itera = 1
        name_core = legal_name
        while with_the_same_name:
            legal_name = u"{} ({})".format(name_core, itera)
            itera += 1
            with_the_same_name = self.search([
                ("name", "=", legal_name),
                ("sync_model_id", "=", sync_model_id.id),
                ("id", "!=", current_id)]
            )
        return legal_name

    @api.model
    def is_this_document_synced(self, res_model, res_id):
        """
        The method to used in UI to check whether this document is already synced

        Methods:
         * _find_object_folder

        Returns:
         * bool
        """
        return self._find_object_folder(res_model, res_id) and True or False

    @api.model
    def _find_object_folder(self, res_model, res_id):
        """
        The method to find object folder of this record

        Args:
         * res_model -  model name
         * res_id - id of record

        Returns:
         * False: if no folder is found
         * sync.object object of found folder otherwise

        Extra info:
         * We rely upon a general principle one object has a single cloud folder
        """
        folder_id = self.search([("sync_model_id.model", "=", res_model), ("res_id", "=", res_id)], limit=1,)
        return folder_id

    @api.model
    def _create_default_folders_inside(self, parent_key, parent_path, folders):
        """
        The method to create folders default for this model

        Args:
         * parent_key
         * parent_path
         * folders - string which represents list of folders dict with keys:
           ** id
           ** text - folder_name
           ** icon
           ** children - array with the same key
        """
        folders = json.loads(folders)
        self._create_default_folders_recursive(parent_key=parent_key, parent_path=parent_path, folders=folders)

    @api.model
    def _create_default_folders_recursive(self, parent_key, parent_path, folders):
        """
        The method to create folders default for this model with all child levels

        Args:
         * parent_key
         * parent_path
         * folders - list of folders dict with keys:
           ** id
           ** text - folder_name
           ** icon
           ** children - array with the same keys

        Methods:
         * remove_illegal_characters of ir.attachment

        Extra info:
         * name uniqueness is managed on the widget level
        """
        ir_attachment = self.env["ir.attachment"]
        for folder in folders:
            folder_name = ir_attachment.remove_illegal_characters(folder.get("text"))
            key, path = ir_attachment._create_folder(
                folder_name=folder_name,
                parent_folder_key=parent_key,
                parent_folder_path=parent_path,
            )
            self._create_default_folders_recursive(parent_key=key, parent_path=path, folders=folder.get("children"))

    @api.model
    def _create_and_send(self, sync_model_id, res_model, res_id):
        """
        The method to generate a new object folder in cloud and save link in Odoo in a NEW Odoo folder

        Args:
         * sync_model_id - sync.model object
         * res_model -  model name
         * res_id - id of record

        Methods:
         * _return_folder_name
         * _create_folder of ir.attachment
         * create
         * _create_default_folders_inside

        Returns:
         * sync.object object
        """
        name = self._return_folder_name(
            res_model=res_model,
            res_id=res_id,
            sync_model_id=sync_model_id,
            current_id=False,
        )
        key, path = self.env["ir.attachment"]._create_folder(
            folder_name=name,
            parent_folder_key=sync_model_id.key,
            parent_folder_path=sync_model_id.path,
        )
        new_folder_id = False
        today_now = fields.Datetime.now()
        if key and path:
            new_folder_id = self.create({
                "name": name,
                "sync_model_id": sync_model_id.id,
                "res_id": res_id,
                "key": key,
                "path": path,
                "last_sync_datetime": today_now,
            })
            self._cr.commit()
            if sync_model_id and sync_model_id.default_folders and sync_model_id.default_folders != "[]":
                self._create_default_folders_inside(
                    parent_key=key,
                    parent_path=path,
                    folders=sync_model_id.default_folders,
                )
        return new_folder_id

    def _write_and_send(self, sync_model_id):
        """
        The method to create a new object folder in cloud and save link in Odoo in an EXISTING Odoo folder
        We try to update both name / parent, since such object is not reconcilled.
        That is why we also have sync_model_id in args

        Args:
         * sync_model_id - sync.model object
         * res_model -  model name
         * res_id - id of record

        Methods:
         * _return_folder_name
         * _create_folder of ir.attachment
         * create
         * _create_default_folders_inside

        Returns:
         * sync.object object
        """
        for sync_object in self:
            name = self._return_folder_name(
                res_model=sync_object.sync_model_id.model,
                res_id=sync_object.res_id,
                sync_model_id=sync_object.sync_model_id,
                current_id=sync_object.id,
            )
            key, path = self.env["ir.attachment"]._create_folder(
                folder_name=name,
                parent_folder_key=sync_model_id.key,
                parent_folder_path=sync_model_id.path,
            )
            new_folder_id = False
            today_now = fields.Datetime.now()
            if key and path:
                new_folder_id = self.write({
                    "name": name,
                    "sync_model_id": sync_model_id.id,
                    "key": key,
                    "path": path,
                    "last_sync_datetime": today_now,
                })
                self._cr.commit()
                if sync_object.sync_model_id and sync_object.sync_model_id.default_folders and \
                        sync_object.sync_model_id.default_folders != "[]":
                    self._create_default_folders_inside(
                        parent_key=key,
                        parent_path=path,
                        folders=sync_model_id.default_folders,
                    )

    def _reconcile_object_folder(self, sync_model_id, client_name, client_path):
        """
        The method to check whether an object folders need update / move and proceed those actions
          0. In case path is changed, we should update it before changes
          1. If parent folder is changed: need to move object folder to another parent
          2. If object name is changed, cloud folder name should be also updated
          3. In case a parent folder doesn't exist, we leave a folder in the last location (and log it)
             Besides, add 'Not synced' in name

        Args:
         * sync_model_id - new sync.model (might be the same as old one)
         * client_name - updated client name
         * client_path - current path of a folder

        Methods:
         * _move_folder
         * _return_folder_name
         * _update_folder

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        folder_id = self
        # 0
        if folder_id.path != client_path:
            folder_id.path = client_path
        # 1
        if sync_model_id != folder_id.sync_model_id:
            folder_id._move_folder(new_parent=sync_model_id,)
        # 2
        folder_name = self._return_folder_name(
            res_model=folder_id.sync_model_id.model,
            res_id=folder_id.res_id,
            sync_model_id=folder_id.sync_model_id,
            current_id=folder_id.id,
        )
        if folder_name != client_name:
            folder_id._update_folder(new_name=folder_name)
        self._cr.commit()

    def _update_folder(self, new_name):
        """
        The method to update folder in cloud

        Args:
         * new_name - char

        Methods:
         * _update_folder of ir.attachment
         * write
        """
        ir_attachment = self.env["ir.attachment"]
        today_now = fields.Datetime.now()
        for sync_object in self:
            key, path = ir_attachment._update_folder(
                folder_id=sync_object,
                new_folder_name=new_name,
            )
            if key and path:
                sync_object.write({
                    "key": key,
                    "path": path,
                    "name": new_name,
                    "last_sync_datetime": today_now,
                })

    def _move_folder(self, new_parent):
        """
        The method to move a folder to another one in cloud
        This is dummy method to be overwritten in related client

        Args:
         * new_parent -  sync.model object
        """
        ir_attachment = self.env["ir.attachment"]
        today_now = fields.Datetime.now()
        for sync_object in self:
            key, path = ir_attachment._move_folder(
                folder_id=sync_object,
                new_parent_key=new_parent.key,
                new_parent_path=new_parent.path,
            )
            if key and path:
                sync_object.write({
                    "key": key,
                    "path": path,
                    "sync_model_id": new_parent.id,
                    "last_sync_datetime": today_now,
                })

    def _delete_object_folder(self):
        """
        Method to completely remove object folder and unlink this record

        Methods:
         * _remove_folder of ir.attachment
         * unlink
        """
        ir_attachment = self.env["ir.attachment"]
        for sync_object in self:
            res = ir_attachment._remove_folder(folder_id=sync_object)
            if res:
                sync_object.unlink()
                self._cr.commit()

    def _return_children(self):
        """
        The method to return all child elements of this folder in Client

        Methods:
         * _return_child_items of ir.attachment

        Returns:
         * list of of child dicts including name, id, webUrl
         * None if error

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        ir_attachment = self.env["ir.attachment"]
        child_ids = ir_attachment._return_child_items(folder_id=self)
        return child_ids
